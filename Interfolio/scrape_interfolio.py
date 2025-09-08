#!/usr/bin/env python3
"""
Interfolio Documentation Scraper for RAG Server
Scrapes documentation from product-help.interfolio.com and saves as markdown files
"""

import os
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from loguru import logger
from markdownify import markdownify as md
from requests_html import HTMLSession
from tqdm.contrib.concurrent import thread_map

# Configure loguru
logger.add("scraper.log", rotation="10 MB", retention="10 days")


class InterfolioScraper:
    def __init__(self, base_url, output_dir="scraped_content", max_workers=8):
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.visited_urls = set()
        self.failed_urls = set()
        self.domain = urlparse(base_url).netloc

        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # HTML session for requests_html
        self.session = HTMLSession()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def get_session(self):
        """Return the HTML session instance"""
        return self.session

    def render_js_content(self, response, timeout=10):
        """Render JavaScript content using requests_html"""
        try:
            # Render JavaScript content
            response.html.render(timeout=timeout)
            # Additional wait for dynamic content
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Failed to render JavaScript content: {e}")

    def extract_text_content(self, soup):
        """Extract text content from BeautifulSoup object, removing all links"""
        # Remove all anchor tags but keep their text
        for a in soup.find_all("a"):
            a.replace_with(a.get_text() or "")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def html_to_markdown(self, html_content):
        """Convert HTML to markdown, removing all links"""
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove navigation, headers, footers, etc.
        for element in soup.find_all(["nav", "header", "footer", "aside"]):
            element.decompose()

        # Remove common footer patterns
        for element in soup.find_all(
            text=re.compile(r"Was this article helpful\?", re.IGNORECASE)
        ):
            parent = element.parent
            while parent and parent.name not in ("section", "div", "article"):
                parent = parent.parent
            if parent:
                parent.decompose()

        # Remove "Related Articles" sections
        for element in soup.find_all(
            text=re.compile(r"Related Articles", re.IGNORECASE)
        ):
            parent = element.parent
            while parent and parent.name not in ("section", "div", "article"):
                parent = parent.parent
            if parent:
                parent.decompose()

        # Find main content area
        main_content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_="content")
            or soup.body
        )

        if not main_content:
            return ""

        # Remove all links but keep text
        for a in main_content.find_all("a"):
            a.replace_with(a.get_text() or "")

        # Convert to markdown
        markdown_content = md(str(main_content), heading_style="ATX", bullets="-")

        # Clean up excessive newlines
        return re.sub(r"\n{3,}", "\n\n", markdown_content).strip()

    def generate_filename(self, url, title=None):
        """Generate a safe filename from URL and title"""
        path = urlparse(url).path
        path = path.removesuffix("/")

        if title:
            # Use title for filename
            filename = re.sub(r"[^\w\s-]", "", title.lower())
            filename = re.sub(r"[-\s]+", "-", filename)
        else:
            # Use URL path for filename
            filename = path.replace("/", "_")
            if not filename:
                filename = "index"

        # Ensure unique filename
        base_filename = filename[:100]  # Limit length
        counter = 0
        while True:
            if counter == 0:
                full_filename = f"{base_filename}.md"
            else:
                full_filename = f"{base_filename}_{counter}.md"

            filepath = os.path.join(self.output_dir, full_filename)
            if not Path(filepath).exists():
                return full_filename
            counter += 1

    def scrape_page(self, url):
        """Scrape a single page and save as markdown"""
        if url in self.visited_urls or url in self.failed_urls:
            return []

        logger.info(f"Scraping: {url}")
        self.visited_urls.add(url)

        try:
            # Get page using requests_html
            response = self.session.get(url)
            response.raise_for_status()

            # Render JavaScript if needed
            self.render_js_content(response)

            # Get HTML content
            html_content = response.html.html
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract title
            title = soup.find("title")
            title_text = title.get_text() if title else "Untitled"

            # Convert to markdown
            markdown_content = self.html_to_markdown(html_content)

            if markdown_content:
                # Save to file
                filename = self.generate_filename(url, title_text)
                filepath = os.path.join(self.output_dir, filename)

                # Add metadata
                metadata = f"title: {title_text}\n\n"

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(metadata + markdown_content)

                logger.info(f"Saved: {filename}")

            # Find internal links to scrape
            internal_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                parsed = urlparse(absolute_url)

                # Only follow internal links
                if (
                    parsed.netloc == self.domain
                    and absolute_url not in self.visited_urls
                ):
                    # Skip certain file types
                    if not any(
                        absolute_url.endswith(ext)
                        for ext in (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip")
                    ):
                        internal_links.append(absolute_url)

            return list(set(internal_links))

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.failed_urls.add(url)
            return []

    def scrape_site(self):
        """Scrape the entire site starting from base URL"""
        logger.info(f"Starting scrape of {self.base_url}")
        urls_to_scrape = [self.base_url]

        while urls_to_scrape:
            # Process current batch of URLs using thread_map
            current_batch = urls_to_scrape[: self.max_workers]
            urls_to_scrape = urls_to_scrape[self.max_workers :]

            # Scrape current batch with progress bar
            batch_results = thread_map(
                self.scrape_page,
                current_batch,
                max_workers=self.max_workers,
                desc=f"Scraping batch ({len(self.visited_urls)} pages completed)",
            )

            # Add new URLs to queue from batch results
            for new_urls in batch_results:
                if new_urls:  # scrape_page returns list of URLs or empty list
                    for url in new_urls:
                        if url not in self.visited_urls and url not in urls_to_scrape:
                            urls_to_scrape.append(url)

        logger.info(f"Scraping complete. Scraped {len(self.visited_urls)} pages.")
        logger.info(f"Failed URLs: {len(self.failed_urls)}")

        # Save failed URLs for reference
        if self.failed_urls:
            with open(os.path.join(self.output_dir, "failed_urls.txt"), "w") as f:
                for url in self.failed_urls:
                    f.write(f"{url}\n")


def main():
    """Main function"""
    # Configuration
    base_url = "https://product-help.interfolio.com/en_US/technical-resources/about-interfolio-apis-and-documentation"
    output_dir = "interfolio_docs"
    max_workers = 24  # Adjust based on your system resources

    # Create scraper instance
    scraper = InterfolioScraper(base_url, output_dir, max_workers)

    try:
        # Start scraping
        scraper.scrape_site()

        # Summary
        logger.info("\nScraping completed!")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Total pages scraped: {len(scraper.visited_urls)}")
        logger.info(f"Failed pages: {len(scraper.failed_urls)}")

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
