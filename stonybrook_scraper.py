"""
stonybrook_scraper.py

Crawl all pages under https://www.stonybrook.edu/*, convert each to markdown,
excluding headers, footers, and navs, and save as separate .md files in stonybrook_content.
Respects robots.txt and skips PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, PNG, JPG, JPEG files.

Dependencies: requests, beautifulsoup4, markdownify
"""
import os
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Config
START_URL = "https://www.stonybrook.edu/"
ALLOWED_DOMAIN = "www.stonybrook.edu"
ALLOWED_URL_PREFIX = "https://www.stonybrook.edu/"
OUTPUT_DIR = "stonybrook_content"
VISITED_FILE = "visited.txt"
QUEUE_FILE = "queue.txt"
REQUEST_TIMEOUT = 10  # seconds
SLEEP_TIME = 1.5

# File extensions to skip
SKIP_EXTENSIONS = [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"]

# Setup
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Setup robots.txt parser
ROBOTS_URL = f"{ALLOWED_URL_PREFIX}robots.txt"
USER_AGENT = "*"
rp = urllib.robotparser.RobotFileParser()
rp.set_url(ROBOTS_URL)
try:
    rp.read()
    print("✅ robots.txt loaded.")
except Exception as e:
    print(f"⚠️  Could not read robots.txt: {e}")
    rp = None  # Fail open: allow everything

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


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove all header, footer, nav tags
    for tag in soup.find_all(['header', 'footer', 'nav']):
        tag.decompose()

    # Try multiple selectors for main content
    selectors = [('main', {}), ('div', {'role': 'main'}), ('div', {'class': 'region-content'}), ('article', {}),
        ('div', {'id': 'content'})]
    main_content = None
    for tag, attrs in selectors:
        found = soup.find(tag, attrs=attrs)
        if found:
            main_content = found
            break

    # Fallback to <body> if nothing else
    if not main_content:
        main_content = soup.find("body")
    if not main_content:
        # If literally nothing found, return empty string
        return ""

    # Remove all script/style in main content
    for el in main_content.find_all(['script', 'style']):
        el.decompose()

    # Markdownify
    markdown = md(str(main_content), heading_style="ATX")
    return markdown.strip()


try:
    while queue:
        url = queue.pop(0)
        url_no_fragment = urlparse(url)._replace(fragment="").geturl()
        if url_no_fragment in visited:
            continue

        # robots.txt check before crawling
        if rp is not None and not rp.can_fetch(USER_AGENT, url_no_fragment):
            print(f"🚫 Blocked by robots.txt: {url_no_fragment}")
            continue

        print(f"🔍 Crawling: {url_no_fragment}")
        visited.add(url_no_fragment)

        # Save to visited log
        with open(VISITED_FILE, "a", encoding="utf-8") as f:
            f.write(url_no_fragment + "\n")

        try:
            resp = requests.get(url_no_fragment, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️  Skipping {url_no_fragment!r}: {e}")
            continue

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Enqueue internal links, skip docs, keep to allowed domain and prefix
        for a in soup.find_all("a", href=True):
            href = urljoin(url_no_fragment, a["href"])
            parsed = urlparse(href)
            # Remove fragment (anchor)
            href_no_fragment = parsed._replace(fragment="").geturl()
            path = parsed.path.lower()
            # Skip unwanted extensions anywhere in path
            if any(ext in path for ext in SKIP_EXTENSIONS):
                continue
            # Only allow within allowed domain and prefix
            if (parsed.netloc == ALLOWED_DOMAIN and href_no_fragment.startswith(ALLOWED_URL_PREFIX)
                and href_no_fragment not in visited and href_no_fragment not in queue):
                # Check robots.txt before queuing (optional, can remove for speed)
                if rp is not None and not rp.can_fetch(USER_AGENT, href_no_fragment):
                    continue
                queue.append(href_no_fragment)

        try:
            # Clean and extract main content
            markdown = clean_html(html)
            if not markdown or len(markdown) < 50:
                print(f"⚠️  Not enough main content found at {url}, skipping.")
                continue

            # Save file
            parsed_start = urlparse(url)
            path = parsed_start.path.strip("/").replace("/", "_") or "index"
            filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown)

            print(f"✅  Saved {url} → {filepath}")

        except Exception as e:
            print(f"💥 Error processing {url}: {e}")
            continue

        # Save queue after each page
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            for item in queue:
                f.write(item + "\n")

        time.sleep(SLEEP_TIME)

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
