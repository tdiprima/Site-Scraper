#!/usr/bin/env python3
"""
requests_html-based web crawler for The Cancer Imaging Archive website
Handles JavaScript-rendered content using requests_html instead of selenium

Usage:
python tcia-requests-html-crawler.py
"""

import hashlib
import os
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse

import html2text
from loguru import logger
from requests_html import HTMLSession


class TCIARequestsHTMLCrawler:
    def __init__(self, base_url: str, max_depth: int = 3):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth

        # Extensions to skip
        self.skip_extensions = {
            ".pdf",
            ".doc",
            ".docx",
            ".ppt",
            ".pptx",
            ".xls",
            ".xlsx",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".svg",
            ".ico",
            ".webp",
            ".mp4",
            ".mp3",
            ".avi",
            ".mov",
            ".zip",
            ".tar",
            ".gz",
            ".rar",
            ".exe",
            ".dmg",
            ".json",
            ".xml",
            ".csv",
        }

        # Initialize session
        self.session = HTMLSession()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        # Create output directory - DIFFERENT from original to protect existing files
        self.output_dir = "tcia_dynamic_content_only"
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir} (protecting existing files)")

        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True  # Convert links to just their text - NO URLS!
        self.h2t.ignore_images = True
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.skip_internal_links = True  # Skip internal links
        self.h2t.ignore_anchors = True  # Ignore anchor links

        # Track visited URLs
        self.visited = set()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        # Remove fragment
        url = url.split("#")[0]

        # Check if it's within our domain
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False

        # Check file extension
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in self.skip_extensions):
            return False

        return True

    def check_if_dynamic_page(self, initial_html: str, final_html: str) -> bool:
        """Check if page content was loaded dynamically"""
        # Compare content length (dynamic pages usually have much more content after JS)
        initial_len = len(initial_html)
        final_len = len(final_html)

        # If content increased by more than 50%, likely dynamic
        if final_len > initial_len * 1.5:
            return True

        # Check for common signs of dynamic content
        from bs4 import BeautifulSoup

        initial_soup = BeautifulSoup(initial_html, "html.parser")
        final_soup = BeautifulSoup(final_html, "html.parser")

        # Count meaningful content elements
        initial_content = len(
            initial_soup.find_all(["p", "div", "article", "section", "main"])
        )
        final_content = len(
            final_soup.find_all(["p", "div", "article", "section", "main"])
        )

        # If content elements increased significantly, it's dynamic
        return final_content > initial_content * 1.3

    def extract_main_content(self, html_content: str) -> str:
        """Extract main content as text"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")

        # Remove script, style, and navigation elements FIRST
        for tag in soup(
            ["script", "style", "header", "nav", "footer", "aside", "noscript"]
        ):
            tag.decompose()

        # Remove elements by class/id patterns
        nav_patterns = [
            '[class*="header"]',
            '[class*="footer"]',
            '[class*="navbar"]',
            '[class*="navigation"]',
            '[class*="menu"]',
            '[class*="sidebar"]',
            '[class*="breadcrumb"]',
            '[id*="header"]',
            '[id*="footer"]',
            '[id*="nav"]',
            '[id*="menu"]',
            ".top-bar",
            ".bottom-bar",
            ".site-header",
            ".site-footer",
            ".page-header",
            ".page-footer",
        ]

        for pattern in nav_patterns:
            for element in soup.select(pattern):
                element.decompose()

        # Try to find main content area
        main_content = None
        content_selectors = [
            "main",
            "article",
            ".content",
            "#content",
            ".container",
            '[role="main"]',
            ".page-content",
            ".entry-content",
            ".post-content",
            "section",
        ]

        for selector in content_selectors:
            if (
                selector.startswith(".")
                or selector.startswith("#")
                or selector.startswith("[")
            ):
                main_content = soup.select_one(selector)
            else:
                main_content = soup.find(selector)

            if main_content:
                break

        # If no main content found, use body
        if not main_content:
            main_content = soup.body or soup

        if main_content:
            # Convert to markdown
            return self.h2t.handle(str(main_content))
        else:
            return "No content found"

    def save_as_markdown(self, url: str, content: str) -> str:
        """Save content as markdown file"""
        # Create filename from URL
        parsed = urlparse(url)
        path = parsed.path.strip("/")

        if not path:
            filename = "index.md"
        else:
            # Replace slashes with underscores
            filename = path.replace("/", "_") + ".md"

        # Clean filename
        filename = "".join(c for c in filename if c.isalnum() or c in ("_", "-", "."))

        # Add hash if filename already exists
        filepath = os.path.join(self.output_dir, filename)
        if Path(filepath).exists():
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{filename.rsplit('.', 1)[0]}_{url_hash}.md"
            filepath = os.path.join(self.output_dir, filename)

        # Write content
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return None

    def scrape_page(self, url: str) -> set:
        """Scrape a single page and return found URLs"""
        try:
            logger.info(f"Checking: {url}")

            # Get the page with requests_html
            r = self.session.get(url, timeout=30)
            initial_html = r.text

            # Render JavaScript - this is equivalent to Selenium's wait for content
            try:
                r.html.render(timeout=20, wait=2, sleep=2)
                final_html = r.html.html
            except Exception as e:
                logger.warning(f"JavaScript rendering failed for {url}: {e}")
                final_html = initial_html

            # Check if this is a dynamic page
            if not self.check_if_dynamic_page(initial_html, final_html):
                logger.info(f"Skipping {url} - not dynamically loaded")
                # Still extract links for crawling
                found_urls = set()
                for link in r.html.links:
                    if not link.startswith(("javascript:", "mailto:", "tel:", "#")):
                        absolute_url = urljoin(url, link).split("#")[0]
                        if (
                            self.is_valid_url(absolute_url)
                            and absolute_url not in self.visited
                        ):
                            found_urls.add(absolute_url)
                return found_urls

            logger.info(f"Dynamic content detected - scraping: {url}")

            # Find all links using requests_html
            found_urls = set()
            for link in r.html.links:
                # Skip non-http links
                if link.startswith(("javascript:", "mailto:", "tel:", "#")):
                    continue

                # Convert to absolute URL
                absolute_url = urljoin(url, link)
                absolute_url = absolute_url.split("#")[0]  # Remove fragments

                # Check if valid and not visited
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                    found_urls.add(absolute_url)

            # Extract and save content
            content = self.extract_main_content(final_html)

            # Check if we got actual content
            if content and len(content.strip()) > 50:  # More than 50 chars
                filepath = self.save_as_markdown(url, content)
                if filepath:
                    logger.info(
                        f"Saved: {os.path.basename(filepath)} ({len(content)} chars)"
                    )
            else:
                logger.warning(f"Little/no content found for {url}")

            return found_urls

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return set()

    def crawl(self):
        """Main crawling function"""
        # Start with homepage and browse-collections
        start_urls = [self.base_url, urljoin(self.base_url, "/browse-collections/")]

        # Initialize queue
        queue = deque()
        for url in start_urls:
            queue.append((url, 0))
            self.visited.add(url)

        processed = 0

        # Process queue
        while queue and processed < 500:  # Limit to 500 pages for safety
            url, depth = queue.popleft()

            if depth > self.max_depth:
                continue

            # Scrape page
            found_urls = self.scrape_page(url)
            processed += 1

            # Add new URLs to queue
            for new_url in found_urls:
                if new_url not in self.visited:
                    queue.append((new_url, depth + 1))
                    self.visited.add(new_url)

            # Progress report
            if processed % 10 == 0:
                logger.info(
                    f"Progress: {processed} pages scraped, {len(queue)} in queue"
                )

        # Final report
        files = os.listdir(self.output_dir)
        logger.info("Crawling complete!")
        logger.info(f"Pages scraped: {processed}")
        logger.info(f"Files created: {len(files)}")


def main():
    """Main function"""
    logger.info("Starting TCIA requests_html crawler")
    logger.info("This crawler handles JavaScript-rendered content using requests_html")

    crawler = TCIARequestsHTMLCrawler(
        base_url="https://www.cancerimagingarchive.net/",
        max_depth=2,  # Start with depth 2
    )

    try:
        crawler.crawl()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
