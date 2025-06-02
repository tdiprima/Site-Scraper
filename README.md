## 🧠 Stony Brook Web Content Scraper

<!-- Disco Theme (Animated) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

Here's a single Python script (`run_full_pipeline.py`) that'll:

1. **Run** the scraper and generate Markdown in an output dir.
2. **Create a new `cleaned_markdown` dir** and process all `.md` files, stripping links/images and saving cleaned files there.
3. **Run header/footer cleanup** on all files in the `cleaned_markdown` dir.

You get a nice, repeatable pipeline with clean separation at each stage. **No manual copying. No moving scripts around. One command.**

## 📋 How to Use

1. In your terminal, just run:

   ```bash
   python3 run_full_pipeline.py
   ```

2. Your **fully cleaned files** will show up in the `cleaned_markdown` directory.

## 💡 Notes

* This script doesn't care where you are, as long as all scripts are together.
* It will **nuke old output/cleaned directories** each time for a clean run.
* If you want to preserve your raw/cleaned files, just comment out or adjust the `shutil.rmtree` lines.

---

Here's a Python script using Crawl4AI to crawl the Stony Brook University website, extracting main content while respecting the specified requirements: `stonybrook_scraper.py`

This script:

1. Uses Crawl4AI to crawl starting from https://www.stonybrook.edu/
2. Respects robots.txt when available
3. Ignores specified file extensions
4. Removes headers, footers, and navigation elements
5. Extracts main content using BeautifulSoup
6. Saves content to markdown files in a "stonybrook_content" directory
7. Limits crawling depth to avoid excessive scraping
8. Creates clean markdown files without URLs in the content

Make sure to install required packages:

```bash
pip install crawl4ai beautifulsoup4
```

The script will create a directory called "stonybrook_content" with markdown files containing the cleaned main content from each page. Each file is named based on the URL's last segment and contains the page's main textual content without headers, footers, or navigation elements.
