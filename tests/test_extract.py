from site_scraper.config import ExtractConfig
from site_scraper.extract import extract_links, html_to_markdown

PAGE = """
<html><body>
  <header><h1>Site Name</h1></header>
  <nav id="top-nav"><a href="/a">A</a></nav>
  <div class="cookie-banner">We use cookies</div>
  <main>
    <h1>Admissions</h1>
    <h2>Quick Links</h2>
    <p>Apply by <a href="/deadlines">the deadline</a> to be considered.</p>
    <p>Skip to main content</p>
    <table><tr><td>Fall</td><td>Jan 15</td></tr></table>
    <script>track()</script>
  </main>
  <footer>Copyright</footer>
</body></html>
"""


def test_keeps_main_content_and_drops_boilerplate():
    md = html_to_markdown(PAGE, ExtractConfig())
    assert "# Admissions" in md
    assert "Site Name" not in md
    assert "Copyright" not in md
    assert "track()" not in md


def test_strip_links_keeps_text():
    md = html_to_markdown(PAGE, ExtractConfig())
    assert "Apply by the deadline to be considered." in md
    assert "/deadlines" not in md


def test_links_kept_when_not_stripping():
    md = html_to_markdown(PAGE, ExtractConfig(strip_links=False))
    assert "[the deadline](/deadlines)" in md


def test_class_and_id_patterns():
    html = '<body><div class="Cookie-Banner">cookies</div><div id="sideBar">side</div><p>body text</p></body>'
    cfg = ExtractConfig(remove_class_patterns=["banner"], remove_id_patterns=["sidebar"])
    assert html_to_markdown(html, cfg) == "body text"


def test_nested_matches_do_not_crash():
    html = '<body><div class="menu"><div class="menu-item"><nav>x</nav></div></div><p>kept</p></body>'
    cfg = ExtractConfig(remove_class_patterns=["menu"])
    assert html_to_markdown(html, cfg) == "kept"


def test_heading_and_line_patterns():
    cfg = ExtractConfig(
        remove_heading_patterns=["quick links"], drop_line_patterns=["skip to main content"]
    )
    md = html_to_markdown(PAGE, cfg)
    assert "Quick Links" not in md
    assert "Skip to main content" not in md
    assert "# Admissions" in md


def test_lone_h1_survives_heading_patterns():
    md = html_to_markdown(PAGE, ExtractConfig(remove_heading_patterns=["admissions"]))
    assert "# Admissions" in md


def test_flatten_tables():
    md = html_to_markdown(PAGE, ExtractConfig(flatten_tables=True))
    assert "Fall Jan 15" in md
    assert "|" not in md


def test_link_density_removes_link_lists():
    links = "".join(f'<li><a href="/{i}">Link {i}</a></li>' for i in range(8))
    html = f"<body><ul>{links}</ul><p>Real paragraph of content.</p></body>"
    md = html_to_markdown(html, ExtractConfig(link_density_threshold=0.7))
    assert md == "Real paragraph of content."


def test_content_selector_fallback_to_body():
    md = html_to_markdown("<body><p>hello</p></body>", ExtractConfig(content_selectors=["main"]))
    assert md == "hello"


def test_extract_links_resolves_and_dedupes():
    html = '<a href="/a#top">1</a><a href="a">2</a><a href="https://other.example/x">3</a>'
    assert extract_links(html, "https://example.com/") == [
        "https://example.com/a",
        "https://other.example/x",
    ]
