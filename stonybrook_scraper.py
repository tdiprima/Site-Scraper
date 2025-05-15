#!/usr/bin/env python3
"""
Crawl all pages under *.stonybrookmedicine.edu starting from the BMI home,
convert each to markdown (excluding headers/footers), and save as separate .md files.
Supports resume on Ctrl+C using visited.txt and queue.txt.
"""

import os
import sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Config
START_URL = "https://bmi.stonybrookmedicine.edu"
ALLOWED_DOMAIN = "stonybrookmedicine.edu"
OUTPUT_DIR = "output_markdown"
VISITED_FILE = "visited.txt"
QUEUE_FILE = "queue.txt"
REQUEST_TIMEOUT = 10  # seconds

# Setup
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load or initialize visited set
if os.path.exists(VISITED_FILE):
    with open(VISITED_FILE, "r", encoding="utf-8") as f:
        visited = set(line.strip() for line in f if line.strip())
else:
    visited = set()

# Load or initialize queue
if os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        queue = [line.strip() for line in f if line.strip()]
else:
    queue = [START_URL]

print("🚀 Starting crawl...\n(Press Ctrl+C to stop anytime)\n")

try:
    while queue:
        url = queue.pop(0)
        if url in visited:
            continue
        print(f"🔍 Crawling: {url}")
        visited.add(url)

        # Save to visited log
        with open(VISITED_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")

        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️  Skipping {url!r}: {e}")
            continue

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Enqueue internal links
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            parsed = urlparse(href)
            if ALLOWED_DOMAIN in parsed.netloc and href not in visited and href not in queue:
                queue.append(href)

        try:
            # Extract main content
            main_content = soup.find("div", class_="region-content")
            if not main_content:
                print(f"⚠️  No main content found at {url}, skipping.")
                continue

            # Convert to Markdown
            markdown = md(str(main_content), heading_style="ATX")

            # Save file
            parsed_start = urlparse(url)
            path = parsed_start.path.strip("/").replace("/", "_") or "index"
            filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {parsed_start.netloc}{parsed_start.path}\n\n")
                f.write(markdown)

            print(f"✅  Saved {url} → {filepath}")

        except RecursionError:
            print(f"💥 RecursionError on {url}, saving as raw HTML instead.")
            path = parsed_start.path.strip("/").replace("/", "_") or "index"
            filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.html"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)

except KeyboardInterrupt:
    print("\n🛑 Crawl interrupted by user. Saving queue and exiting...\n")

finally:
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        for item in queue:
            f.write(item + "\n")

    print(f"📁 Queue saved to {QUEUE_FILE}")
    print(f"📁 Visited URLs saved to {VISITED_FILE}")
    print("👋 Bye!")
    sys.exit(0)
