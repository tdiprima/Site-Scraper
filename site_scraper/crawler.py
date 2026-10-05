"""Polite, resumable, multi-threaded crawler.

Stays inside the configured URL prefix, honours robots.txt (including
Crawl-delay), rate-limits globally, and can be stopped and resumed: progress
is kept in `<output_dir>/.crawl/`.
"""

import hashlib
import logging
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

from .config import SiteConfig
from .extract import extract_links, html_to_markdown

log = logging.getLogger(__name__)

MAX_FILENAME_STEM = 200


def url_to_filename(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    stem = f"{parsed.netloc.replace('.', '_').replace(':', '_')}_{path}"
    if len(stem) > MAX_FILENAME_STEM:
        digest = hashlib.sha1(url.encode()).hexdigest()[:8]
        stem = f"{stem[:MAX_FILENAME_STEM]}_{digest}"
    return f"{stem}.md"


class Crawler:
    def __init__(self, site: SiteConfig, session: requests.Session | None = None):
        self.site = site
        self.cfg = site.crawl
        self.output_dir = Path(site.output_dir)
        self.visited_file = site.state_dir / "visited.txt"
        self.queue_file = site.state_dir / "queue.tsv"

        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = self.cfg.user_agent

        self.delay = self.cfg.delay
        self.robots: RobotFileParser | None = None

        self._queue: Queue[tuple[str, int]] = Queue()
        self._seen: set[str] = set()
        self._leftover: list[tuple[str, int]] = []
        self._lock = threading.Lock()
        self._rate_lock = threading.Lock()
        self._next_request = 0.0
        self._stop = threading.Event()
        self.fetched = 0
        self.saved = 0

    # -- URL rules ---------------------------------------------------------

    def in_scope(self, url: str) -> bool:
        # Scheme-insensitive: sites often redirect between http and https.
        url = url.split("://", 1)[-1]
        prefix = self.site.allowed_prefix.split("://", 1)[-1]
        return url.startswith(prefix) or url == prefix.rstrip("/")

    def should_skip(self, url: str) -> bool:
        parsed = urlparse(url)
        if self.cfg.skip_query_strings and parsed.query:
            return True
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in self.cfg.skip_extensions):
            return True
        lowered = url.lower()
        return any(p.lower() in lowered for p in self.cfg.skip_url_patterns)

    def allowed(self, url: str) -> bool:
        if not self.in_scope(url) or self.should_skip(url):
            return False
        return self.robots is None or self.robots.can_fetch(self.cfg.user_agent, url)

    # -- robots.txt --------------------------------------------------------

    def _load_robots(self) -> None:
        robots_url = urljoin(self.site.start_url, "/robots.txt")
        parser = RobotFileParser(robots_url)
        try:
            resp = self.session.get(robots_url, timeout=self.cfg.timeout)
        except requests.RequestException as e:
            log.warning("Could not fetch robots.txt (%s); assuming no restrictions", e)
            return
        if resp.status_code in (401, 403):
            parser.parse(["User-agent: *", "Disallow: /"])
        elif resp.ok:
            parser.parse(resp.text.splitlines())
        else:
            return
        self.robots = parser
        crawl_delay = parser.crawl_delay(self.cfg.user_agent)
        if crawl_delay and float(crawl_delay) > self.delay:
            self.delay = float(crawl_delay)
            log.info("Using robots.txt Crawl-delay of %ss", self.delay)

    # -- state -------------------------------------------------------------

    def _load_state(self) -> None:
        if self.visited_file.exists():
            self._seen.update(self.visited_file.read_text(encoding="utf-8").split())
        pending = []
        if self.queue_file.exists():
            for line in self.queue_file.read_text(encoding="utf-8").splitlines():
                depth, _, url = line.partition("\t")
                if url and url not in self._seen:
                    pending.append((url, int(depth)))
        if pending:
            log.info("Resuming: %d visited, %d queued", len(self._seen), len(pending))
        elif self._seen:
            log.info("Nothing left to crawl (%d pages already visited)", len(self._seen))
        else:
            pending = [(self.site.start_url, 0)]
        for url, depth in pending:
            self._seen.add(url)
            self._queue.put((url, depth))

    def _save_queue(self) -> None:
        remaining = list(self._leftover)
        while True:
            try:
                remaining.append(self._queue.get_nowait())
            except Empty:
                break
        self.queue_file.write_text(
            "".join(f"{depth}\t{url}\n" for url, depth in remaining), encoding="utf-8"
        )
        if remaining:
            log.info("Stopped with %d URLs queued; run again to resume", len(remaining))

    # -- crawling ----------------------------------------------------------

    def _throttle(self) -> None:
        with self._rate_lock:
            wait = self._next_request - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._next_request = time.monotonic() + self.delay

    def _process(self, url: str, depth: int) -> None:
        with self._lock:
            if self.cfg.max_pages and self.fetched >= self.cfg.max_pages:
                self._leftover.append((url, depth))
                self._stop.set()
                return
            self.fetched += 1

        self._throttle()
        try:
            resp = self.session.get(url, timeout=self.cfg.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            log.warning("Skipping %s: %s", url, e)
            return
        finally:
            with self._lock, open(self.visited_file, "a", encoding="utf-8") as f:
                f.write(url + "\n")

        if "html" not in resp.headers.get("Content-Type", "html"):
            return
        if not self.in_scope(resp.url):
            log.info("Skipping %s: redirected out of scope to %s", url, resp.url)
            return

        html = resp.text
        if depth < self.cfg.max_depth:
            for link in extract_links(html, resp.url):
                with self._lock:
                    if link not in self._seen and self.allowed(link):
                        self._seen.add(link)
                        self._queue.put((link, depth + 1))

        markdown = html_to_markdown(html, self.site.extract)
        if len(markdown) < self.site.extract.min_chars:
            log.info("Skipping %s: not enough content", url)
            return
        if self.site.extract.source_comment:
            markdown = f"<!-- Source: {url} -->\n\n{markdown}"
        path = self.output_dir / url_to_filename(url)
        path.write_text(markdown + "\n", encoding="utf-8")
        with self._lock:
            self.saved += 1
        log.info("[depth %d] %s -> %s", depth, url, path.name)

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                url, depth = self._queue.get(timeout=0.5)
            except Empty:
                # Nothing queued and nothing in flight: the crawl is finished.
                if self._queue.unfinished_tasks == 0:
                    return
                continue
            try:
                self._process(url, depth)
            except Exception:
                log.exception("Error processing %s", url)
            finally:
                self._queue.task_done()

    def run(self) -> int:
        """Crawl until done, interrupted, or max_pages is hit. Returns pages saved."""
        self.site.state_dir.mkdir(parents=True, exist_ok=True)
        self._load_robots()
        if not self.allowed(self.site.start_url):
            raise RuntimeError(
                f"start_url {self.site.start_url} is out of scope, matches a skip "
                "rule, or is disallowed by robots.txt"
            )
        self._load_state()

        threads = [
            threading.Thread(target=self._worker, daemon=True)
            for _ in range(max(1, self.cfg.threads))
        ]
        for t in threads:
            t.start()
        try:
            while any(t.is_alive() for t in threads):
                time.sleep(0.2)
        except KeyboardInterrupt:
            log.info("Interrupted; finishing in-flight pages...")
            self._stop.set()
            for t in threads:
                t.join()
        self._save_queue()
        log.info("Fetched %d pages, saved %d to %s", self.fetched, self.saved, self.output_dir)
        return self.saved
