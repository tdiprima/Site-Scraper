"""End-to-end crawler tests against a local HTTP server."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar

import pytest

from site_scraper.config import CrawlConfig, ExtractConfig, SiteConfig
from site_scraper.crawler import Crawler, url_to_filename

BODY = "<p>Enough text on this page to pass the minimum content check.</p>"
PAGES = {
    "/": f"""<main><h1>Home</h1>{BODY}
        <a href="/a">a</a> <a href="/b#frag">b</a> <a href="/file.pdf">pdf</a>
        <a href="/secret/x">secret</a> <a href="/a?page=2">query</a>
        <a href="https://elsewhere.invalid/">external</a></main>""",
    "/a": f'<main><h1>Page A</h1>{BODY}<a href="/a/deep">deep</a></main>',
    "/b": f"<main><h1>Page B</h1>{BODY}</main>",
    "/a/deep": f"<main><h1>Deep</h1>{BODY}</main>",
    "/secret/x": f"<main><h1>Secret</h1>{BODY}</main>",
    "/robots.txt": "User-agent: *\nDisallow: /secret/\n",
}


class Handler(BaseHTTPRequestHandler):
    hits: ClassVar[list[str]] = []

    def do_GET(self):
        Handler.hits.append(self.path)
        body = PAGES.get(self.path)
        if body is None:
            self.send_error(404)
            return
        content_type = "text/plain" if self.path == "/robots.txt" else "text/html"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    Handler.hits = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}/"
    httpd.shutdown()


def make_site(url, tmp_path, **crawl):
    crawl = {"threads": 3, "delay": 0, "timeout": 5, **crawl}
    return SiteConfig(
        name="test",
        start_url=url,
        output_dir=str(tmp_path / "out"),
        crawl=CrawlConfig(**crawl),
        extract=ExtractConfig(),
    )


def saved(site):
    """Saved filenames with the 127_0_0_1_<port>_ prefix removed."""
    return sorted(p.name.split("_", 5)[-1] for p in site.state_dir.parent.glob("*.md"))


def test_crawls_in_scope_pages_only(server, tmp_path):
    site = make_site(server, tmp_path)
    assert Crawler(site).run() == 4
    assert saved(site) == ["a.md", "a_deep.md", "b.md", "index.md"]

    fetched = [h for h in Handler.hits if h != "/robots.txt"]
    assert sorted(fetched) == ["/", "/a", "/a/deep", "/b"]  # each once; no pdf/secret/query

    home = next(site.state_dir.parent.glob("*_index.md")).read_text()
    assert home.startswith(f"<!-- Source: {server} -->")
    assert "# Home" in home


def test_max_depth(server, tmp_path):
    site = make_site(server, tmp_path, max_depth=1)
    Crawler(site).run()
    assert saved(site) == ["a.md", "b.md", "index.md"]


def test_resume_after_max_pages(server, tmp_path):
    site = make_site(server, tmp_path, threads=1, max_pages=2)
    assert Crawler(site).run() == 2
    assert (site.state_dir / "queue.tsv").read_text().strip()

    assert Crawler(site).run() == 2
    assert saved(site) == ["a.md", "a_deep.md", "b.md", "index.md"]
    fetched = [h for h in Handler.hits if h != "/robots.txt"]
    assert sorted(fetched) == ["/", "/a", "/a/deep", "/b"]  # nothing refetched

    assert Crawler(site).run() == 0  # finished crawl stays finished


def test_start_url_blocked_by_robots(server, tmp_path):
    site = make_site(server + "secret/x", tmp_path)
    site.allowed_prefix = server
    with pytest.raises(RuntimeError):
        Crawler(site).run()


def test_scope_ignores_scheme(tmp_path):
    crawler = Crawler(make_site("https://example.com/docs/", tmp_path))
    crawler.site.allowed_prefix = "https://example.com/docs/"
    assert crawler.in_scope("http://example.com/docs/page")
    assert crawler.in_scope("https://example.com/docs")
    assert not crawler.in_scope("https://example.com/blog/")
    assert not crawler.in_scope("https://example.com.evil.test/docs/")


def test_url_to_filename():
    assert url_to_filename("https://www.example.com/") == "www_example_com_index.md"
    assert url_to_filename("https://www.example.com/a/b/") == "www_example_com_a_b.md"
    long_name = url_to_filename("https://example.com/" + "x" * 400)
    assert len(long_name) < 255
