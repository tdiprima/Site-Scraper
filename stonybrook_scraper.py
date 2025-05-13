#!/usr/bin/env python3
"""
Crawl all pages under *.stonybrookmedicine.edu starting from the BMI home,
convert each to markdown, and save as separate .md files.
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from markdownify import markdownify as md

# 1. Config
START_URL = "https://bmi.stonybrookmedicine.edu"
ALLOWED_DOMAIN = "stonybrookmedicine.edu"
OUTPUT_DIR = "output_markdown"
REQUEST_TIMEOUT = 10  # seconds

# 2. Prep
os.makedirs(OUTPUT_DIR, exist_ok=True)
visited = set()
queue = [START_URL]

# 3. Crawl
while queue:
    url = queue.pop(0)
    if url in visited:
        continue
    visited.add(url)

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️  Skipping {url!r}: {e}")
        continue

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 3a. Enqueue same-domain links
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        parsed = urlparse(href)
        if ALLOWED_DOMAIN in parsed.netloc and href not in visited:
            queue.append(href)

    try:
        # 4. Convert to Markdown
        markdown = md(html, heading_style="ATX")

        # 5. Write out file
        parsed_start = urlparse(url)

        # sanitize path: / -> index, foo/bar -> foo_bar
        path = parsed_start.path.strip("/").replace("/", "_") or "index"
        filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            # optional: include a header
            f.write(f"# {parsed_start.netloc}{parsed_start.path}\n\n")
            f.write(markdown)

        print(f"✅  Saved {url} → {filepath}")

    except RecursionError:
        print(f"💥 RecursionError on {url}, saving as raw HTML instead.")
        filename = f"{parsed.netloc.replace('.', '_')}_{path}.html"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

print("\n🎉 Done crawling and markdown-ifying!")
