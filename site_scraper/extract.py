"""Turn a fetched HTML page into clean Markdown, driven by ExtractConfig."""

import re
from urllib.parse import urldefrag, urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify

from .config import ExtractConfig

HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]
MD_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")


def extract_links(html: str, base_url: str) -> list[str]:
    """Absolute, fragment-free URLs of every link on the page, in page order."""
    soup = BeautifulSoup(html, "html.parser")
    links = (urldefrag(urljoin(base_url, a["href"])).url for a in soup.find_all("a", href=True))
    return list(dict.fromkeys(links))


def _attr_contains(el, attr: str, patterns: list[str]) -> bool:
    value = el.get(attr) or ""
    if isinstance(value, list):
        value = " ".join(value)
    value = value.lower()
    return any(p in value for p in patterns)


def _remove_boilerplate(soup, cfg: ExtractConfig) -> None:
    # Decomposing a parent also destroys its children, which may still be
    # ahead of us in the result list, hence the `decomposed` checks.
    def removable(el):
        return not el.decomposed and el.name not in ("html", "body")

    for el in soup.find_all(["script", "style", "noscript"]):
        el.decompose()

    for selector in cfg.remove_selectors:
        for el in soup.select(selector):
            if removable(el):
                el.decompose()

    class_patterns = [p.lower() for p in cfg.remove_class_patterns]
    id_patterns = [p.lower() for p in cfg.remove_id_patterns]
    if class_patterns or id_patterns:
        for el in soup.find_all(True):
            if removable(el) and (
                _attr_contains(el, "class", class_patterns)
                or _attr_contains(el, "id", id_patterns)
            ):
                el.decompose()

    if cfg.link_density_threshold > 0:
        for el in soup.find_all(["ul", "ol", "div"]):
            if not removable(el):
                continue
            links = el.find_all("a")
            if len(links) <= 5:
                continue
            link_len = sum(len(a.get_text(strip=True)) for a in links)
            text_len = len(el.get_text(strip=True))
            if link_len and link_len / max(text_len, 1) > cfg.link_density_threshold:
                el.decompose()


def _find_content(soup, cfg: ExtractConfig):
    for selector in cfg.content_selectors:
        found = soup.select_one(selector)
        if found is not None:
            return found
    return soup.body if soup.body is not None else soup


def html_to_markdown(html: str, cfg: ExtractConfig) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _remove_boilerplate(soup, cfg)
    content = _find_content(soup, cfg)

    if cfg.flatten_tables:
        for table in content.find_all("table"):
            table.replace_with(f" {table.get_text(' ', strip=True)} ")

    heading_patterns = [p.lower() for p in cfg.remove_heading_patterns]
    if heading_patterns:
        h1_count = len(content.find_all("h1"))
        for heading in content.find_all(HEADINGS):
            text = heading.get_text(strip=True).lower()
            is_page_title = heading.name == "h1" and h1_count == 1
            if not is_page_title and any(p in text for p in heading_patterns):
                heading.decompose()

    if cfg.strip_links:
        for a in content.find_all("a"):
            if a.decomposed:
                continue
            text = a.get_text()
            # Pad with spaces so adjacent link texts don't run together.
            if text.strip():
                a.replace_with(f" {text} ")
            else:
                a.decompose()

    markdown = markdownify(str(content), heading_style="ATX")
    if cfg.strip_links:
        markdown = MD_LINK.sub(r"\1", markdown)
    if cfg.flatten_tables:
        markdown = markdown.replace("|", " ")

    markdown = re.sub(r"[ \t]+", " ", markdown)
    drop = [p.lower() for p in cfg.drop_line_patterns]
    lines = [line.strip() for line in markdown.split("\n")]
    lines = [line for line in lines if not any(p in line.lower() for p in drop)]
    markdown = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return markdown.strip()
