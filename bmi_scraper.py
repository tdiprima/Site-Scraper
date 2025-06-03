"""
Crawl all pages under https://bmi.stonybrookmedicine.edu/*, convert each to markdown,
excluding headers/footers, and save as separate .md files.
Respects robots.txt and skips PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX files.
"""
import os
import sys
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import urllib.robotparser

# Config
START_URL = "https://bmi.stonybrookmedicine.edu"
ALLOWED_DOMAIN = "bmi.stonybrookmedicine.edu"
ALLOWED_URL_PREFIX = "https://bmi.stonybrookmedicine.edu/"
OUTPUT_DIR = "output_markdown"
VISITED_FILE = "visited.txt"
QUEUE_FILE = "queue.txt"
REQUEST_TIMEOUT = 10  # seconds

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

try:
    while queue:
        url = queue.pop(0)
        if url in visited:
            continue

        # robots.txt check before crawling
        if rp is not None and not rp.can_fetch(USER_AGENT, url):
            print(f"🚫 Blocked by robots.txt: {url}")
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

        # Enqueue internal links, skip docs, keep to allowed domain and prefix
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            parsed = urlparse(href)
            path = parsed.path.lower()
            # Skip unwanted extensions anywhere in path
            if any(ext in path for ext in SKIP_EXTENSIONS):
                continue
            # Only allow within allowed domain and prefix
            if (
                parsed.netloc == ALLOWED_DOMAIN
                and href.startswith(ALLOWED_URL_PREFIX)
                and href not in visited
                and href not in queue
            ):
                # Check robots.txt before queuing (optional, can remove for speed)
                if rp is not None and not rp.can_fetch(USER_AGENT, href):
                    continue
                queue.append(href)

        try:
            # Extract main content
            main_content = soup.find("div", class_="region-content")
            if not main_content:
                print(f"⚠️  No main content found at {url}, skipping.")
                continue

            # Convert to Markdown
            markdown = md(str(main_content), heading_style="ATX")

            # Save file (NO heading with path at top)
            parsed_start = urlparse(url)
            path = parsed_start.path.strip("/").replace("/", "_") or "index"
            filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                # f.write(f"<!-- Source: {parsed_start.netloc}{parsed_start.path} -->\n\n")
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
