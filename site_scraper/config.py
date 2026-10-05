"""Per-site configuration, loaded from a TOML file.

Everything that is specific to one website (URLs, selectors, boilerplate
patterns) lives in the config, so the code stays site-agnostic.
"""

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class CrawlConfig:
    threads: int = 4
    delay: float = 1.0  # minimum seconds between requests, across all threads
    timeout: float = 10.0
    max_depth: int = 5
    max_pages: int = 0  # 0 = unlimited
    user_agent: str = "site-scraper/0.1"
    skip_extensions: list[str] = field(
        default_factory=lambda: [
            ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
            ".mp3", ".mp4", ".zip", ".gz",
        ]
    )  # fmt: skip
    skip_url_patterns: list[str] = field(default_factory=list)
    skip_query_strings: bool = True


@dataclass
class ExtractConfig:
    # First CSS selector that matches becomes the page content; falls back to <body>.
    content_selectors: list[str] = field(
        default_factory=lambda: ["main", "[role=main]", "article"]
    )
    remove_selectors: list[str] = field(
        default_factory=lambda: ["header", "footer", "nav", "aside"]
    )
    # Remove any element whose class / id contains one of these substrings.
    remove_class_patterns: list[str] = field(default_factory=list)
    remove_id_patterns: list[str] = field(default_factory=list)
    # Remove lists/divs where links make up more than this share of the text (0 = off).
    link_density_threshold: float = 0.0
    # Remove headings containing one of these substrings (a lone <h1> is kept).
    remove_heading_patterns: list[str] = field(default_factory=list)
    # Drop Markdown lines containing one of these substrings.
    drop_line_patterns: list[str] = field(default_factory=list)
    strip_links: bool = True
    flatten_tables: bool = False
    source_comment: bool = True
    min_chars: int = 50


@dataclass
class CleanConfig:
    # Regexes removed from every saved file (IGNORECASE | MULTILINE).
    remove_regex: list[str] = field(default_factory=list)
    # Files containing any of these strings are deleted (e.g. soft-404 pages).
    delete_if_contains: list[str] = field(default_factory=list)


@dataclass
class UploadConfig:
    base_url: str = "http://localhost:3000"
    knowledge_id: str = ""
    delay: float = 0.5


@dataclass
class SiteConfig:
    name: str
    start_url: str
    allowed_prefix: str = ""
    output_dir: str = ""
    crawl: CrawlConfig = field(default_factory=CrawlConfig)
    extract: ExtractConfig = field(default_factory=ExtractConfig)
    clean: CleanConfig = field(default_factory=CleanConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)

    def __post_init__(self):
        parsed = urlparse(self.start_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"start_url must be an http(s) URL: {self.start_url!r}")
        if not self.allowed_prefix:
            self.allowed_prefix = f"{parsed.scheme}://{parsed.netloc}/"
        if not self.output_dir:
            self.output_dir = f"output/{self.name}"

    @property
    def state_dir(self) -> Path:
        return Path(self.output_dir) / ".crawl"


def _section(cls, data: dict, name: str):
    raw = data.get(name, {})
    unknown = set(raw) - {f.name for f in fields(cls)}
    if unknown:
        raise ValueError(f"[{name}] unknown keys: {sorted(unknown)}")
    return cls(**raw)


def load_config(path: str | Path) -> SiteConfig:
    path = Path(path)
    with open(path, "rb") as f:
        data = tomllib.load(f)

    sections = {"site", "crawl", "extract", "clean", "upload"}
    unknown = set(data) - sections
    if unknown:
        raise ValueError(f"unknown sections: {sorted(unknown)}")

    site = dict(data.get("site", {}))
    unknown = set(site) - {"name", "start_url", "allowed_prefix", "output_dir"}
    if unknown:
        raise ValueError(f"[site] unknown keys: {sorted(unknown)}")
    if "start_url" not in site:
        raise ValueError("[site] start_url is required")
    site.setdefault("name", path.stem)

    return SiteConfig(
        **site,
        crawl=_section(CrawlConfig, data, "crawl"),
        extract=_section(ExtractConfig, data, "extract"),
        clean=_section(CleanConfig, data, "clean"),
        upload=_section(UploadConfig, data, "upload"),
    )
