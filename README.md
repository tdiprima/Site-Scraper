# Site Scraper

Config-driven website crawler that turns a site into clean Markdown, ready to load into a RAG knowledge base.

Everything specific to one website — start URL, content selectors, boilerplate patterns — lives in a small TOML file, so the crawler itself is site-agnostic.

## Features

- **Polite by default**: honours `robots.txt` (including `Crawl-delay`), rate-limits globally across threads, and stays inside one URL prefix.
- **Resumable**: stop with Ctrl+C or a page limit and run the same command again; visited URLs and the pending queue are kept in `<output_dir>/.crawl/`.
- **Clean output**: strips headers, footers, navigation, link-heavy menus, and scripts, then converts the main content to Markdown with a source-URL comment.
- **Post-processing**: regex-based cleanup of leftover boilerplate and deletion of soft-404 pages.
- **Open WebUI upload**: pushes the Markdown into a knowledge base, resumable.

## Install

Requires Python 3.11+.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```sh
site-scraper crawl sites/example.toml    # crawl and save Markdown to output/example/
site-scraper clean sites/example.toml    # apply the [clean] rules to the saved files
OPENWEBUI_API_KEY=... site-scraper upload sites/example.toml
```

To scrape your own site, copy `sites/example.toml` to `sites/<name>.toml` and edit it. Everything in `sites/` except the example is gitignored, so site-specific configs stay local.

## Configuration

| Section | Key | Purpose |
| --- | --- | --- |
| `[site]` | `start_url` | Where the crawl begins (required) |
| | `allowed_prefix` | Only URLs under this prefix are followed; defaults to the start URL's host |
| | `output_dir` | Where Markdown is written; defaults to `output/<name>` |
| `[crawl]` | `threads`, `delay`, `timeout` | Concurrency and pacing; `delay` is the minimum gap between requests across all threads |
| | `max_depth`, `max_pages` | Crawl limits (`max_pages = 0` means unlimited) |
| | `skip_extensions`, `skip_url_patterns`, `skip_query_strings` | URLs to ignore |
| `[extract]` | `content_selectors` | CSS selectors tried in order for the main content; falls back to `<body>` |
| | `remove_selectors`, `remove_class_patterns`, `remove_id_patterns` | Elements to drop before conversion |
| | `link_density_threshold` | Drop lists/divs that are mostly links (e.g. `0.7`); `0` disables |
| | `remove_heading_patterns`, `drop_line_patterns` | Site-wide headings and lines to drop |
| | `strip_links`, `flatten_tables`, `source_comment`, `min_chars` | Output shaping |
| `[clean]` | `remove_regex` | Regexes removed from every file (case-insensitive, multiline) |
| | `delete_if_contains` | Delete files containing any of these strings |
| `[upload]` | `base_url`, `knowledge_id`, `delay` | Open WebUI target; the API key comes from `OPENWEBUI_API_KEY` |

Unknown keys are rejected, so typos fail fast.

## Development

```sh
pytest
ruff check .
```

The crawler tests run end to end against a local HTTP server; no network access is needed.

## Responsible use

Only crawl sites you are permitted to crawl, keep `delay` generous, and respect each site's terms of use.

## License

MIT — see [LICENSE](LICENSE).

<br>
