from pathlib import Path

import pytest

from site_scraper.clean import clean_dir
from site_scraper.config import CleanConfig, SiteConfig, load_config

EXAMPLE = Path(__file__).parent.parent / "sites" / "example.toml"


def test_example_config_loads():
    site = load_config(EXAMPLE)
    assert site.name == "example"
    assert site.allowed_prefix == "https://quotes.toscrape.com/"
    assert site.output_dir == "output/example"
    assert site.crawl.max_pages == 20


def test_defaults_from_filename(tmp_path):
    cfg = tmp_path / "mysite.toml"
    cfg.write_text('[site]\nstart_url = "https://example.com/docs/"\n')
    site = load_config(cfg)
    assert site.name == "mysite"
    assert site.allowed_prefix == "https://example.com/"
    assert site.state_dir == Path("output/mysite/.crawl")


@pytest.mark.parametrize(
    "body",
    [
        "[crawl]\nthreads = 2\n",  # missing start_url
        '[site]\nstart_url = "https://example.com/"\n[crawl]\nthreadz = 2\n',
        '[site]\nstart_url = "https://example.com/"\n[scrape]\nx = 1\n',
        '[site]\nstart_url = "ftp://example.com/"\n',
    ],
)
def test_invalid_configs_rejected(tmp_path, body):
    cfg = tmp_path / "bad.toml"
    cfg.write_text(body)
    with pytest.raises(ValueError):
        load_config(cfg)


def test_bad_start_url_rejected():
    with pytest.raises(ValueError):
        SiteConfig(name="x", start_url="example.com")


def test_clean_dir(tmp_path):
    (tmp_path / "keep.md").write_text("Search This Site\nReal content\n")
    (tmp_path / "gone.md").write_text("Oops, page not found")
    (tmp_path / "untouched.md").write_text("Nothing to do\n")
    cfg = CleanConfig(remove_regex=[r"^search this site\n"], delete_if_contains=["page not found"])

    assert clean_dir(tmp_path, cfg) == (1, 1)
    assert (tmp_path / "keep.md").read_text() == "Real content\n"
    assert not (tmp_path / "gone.md").exists()
    assert (tmp_path / "untouched.md").read_text() == "Nothing to do\n"
