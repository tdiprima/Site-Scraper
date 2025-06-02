## 🧠 Stony Brook Web Content Scraper

<!-- Disco Theme (Animated) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

### 🔥 Features

* **Domain-wide Markdown Conversion**

  * Scripts like `stonybrook_scraper.py` ⭐️ and `domain_crawler_md_exporter.py` crawl every accessible page under `stonybrookmedicine.edu`, convert them to Markdown using `markdownify`, and save each as a `.md` file. Headers are added for traceability.

* **Async + Headless Crawling**

  * `stonybrook_to_markdown.py` and `get_urls.py` leverage `crawl4ai` with Playwright to crawl pages asynchronously using a BFS strategy with configurable depth and max pages.
  * `crawl_for_ai.py` adds support for non-headless mode on MacOS with extended timeout to handle rendering quirks.

* **Firecrawl Integration**

  * `my_firecrawl.py` supports crawling via Firecrawl’s API. Markdown is auto-extracted from all pages. You’ll need to set the `FIRECRAWL_API_KEY` in your environment.

### 🧹 Cleanup & Post-Processing

* **Markdown Link Simplifier**

  * `clean_markdown_dir.py` strips all Markdown links (`[text](url)`) and images (`![alt](url)`) down to plain text, making the output cleaner for embeddings or AI chunking.

* **Header/Footer Stripping**

  * `header_footer_strip.py` targets repetitive headers like “Skip to main content” and common footers. Just drop it in a directory with your `.md` files and run.

### 🛠 Utilities

* `simple.py` is a minimal working example to test `crawl4ai`.
* Scripts are modular, so you can plug in your preferred crawler/exporter combo and post-process results with the cleaning tools.

### 🗂 Directory Structure

* All output is organized into subfolders like `output_markdown` or `bmi_stonybrook_markdown`.
* Cleaned files get a `_cleaned.md` suffix so originals remain intact.
