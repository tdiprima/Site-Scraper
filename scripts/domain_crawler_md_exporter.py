#!/usr/bin/env python3
"""
python domain_crawler_md_exporter.py \
  --start-url https://bmi.stonybrookmedicine.edu \
  --allowed-domain stonybrookmedicine.edu \
  --output-dir output_markdown
"""
import argparse
import os
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md


def crawl(start_url, allowed_domain, output_dir, max_pages=None):
    os.makedirs(output_dir, exist_ok=True)
    visited = set()
    queue = [start_url]

    while queue and (max_pages is None or len(visited) < max_pages):
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"⚠️  Skipping {url!r}: {e}")
            continue

        html = resp.text
        soup = BeautifulSoup(html, "html.parser")

        # Enqueue new URLs
        for a in soup.find_all("a", href=True):
            href = urljoin(url, a["href"])
            parsed = urlparse(href)
            if allowed_domain in parsed.netloc and href not in visited:
                queue.append(href)

        # Convert to Markdown
        markdown = md(html, heading_style="ATX")

        # Filename logic
        parsed = urlparse(url)
        path = parsed.path.strip("/").replace("/", "_") or "index"
        filename = f"{parsed.netloc.replace('.', '_')}_{path}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {parsed.netloc}{parsed.path}\n\n")
            f.write(markdown)

        print(f"✅  Saved {url} → {filepath}")

    print("\n🎉 Done crawling and markdown-ifying!")


def main():
    parser = argparse.ArgumentParser(description="Crawl a domain, convert HTML pages to markdown, and save to files.")
    parser.add_argument("--start-url", required=True, help="Starting URL")
    parser.add_argument("--allowed-domain", required=True, help="Domain to allow (e.g., stonybrookmedicine.edu)")
    parser.add_argument("--output-dir", default="output_markdown", help="Directory to save markdown files")
    parser.add_argument("--max-pages", type=int, help="Optional max number of pages to crawl")

    args = parser.parse_args()
    crawl(args.start_url, args.allowed_domain, args.output_dir, args.max_pages)


if __name__ == "__main__":
    main()
