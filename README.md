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
