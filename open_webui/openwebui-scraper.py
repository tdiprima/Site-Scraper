import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import markdownify
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RAGOptimizedScraper:
    def __init__(self, base_url, output_dir="scraped_docs", delay=1.0, max_workers=3):
        """
        Initialize the RAG-optimized scraper.

        Args:
            base_url: Starting URL
            output_dir: Directory to save markdown files
            delay: Delay between requests in seconds
            max_workers: Number of worker threads
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.output_dir = output_dir
        self.delay = delay
        self.max_workers = max_workers

        # Thread-safe structures
        self.last_request_time = 0
        self.request_lock = Lock()
        self.processed_urls = set()
        self.process_lock = Lock()

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Set up robots.txt parser
        self.robot_parser = RobotFileParser()
        self.setup_robots_txt()

    def setup_robots_txt(self):
        """Check and parse robots.txt"""
        robots_url = f"https://{self.domain}/robots.txt"
        self.robot_parser.set_url(robots_url)
        try:
            self.robot_parser.read()
            logger.info(f"Successfully loaded robots.txt")
        except:
            logger.warning(f"Could not load robots.txt")

    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        return self.robot_parser.can_fetch("*", url)

    def rate_limited_request(self, url):
        """Make a rate-limited request"""
        with self.request_lock:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                time.sleep(sleep_time)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Compatible; DocsScraper/1.0; Educational Purpose)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            self.last_request_time = time.time()

            return response

    def get_sitemap_urls(self):
        """Parse sitemap.xml to get all URLs"""
        sitemap_url = urljoin(self.base_url, '/sitemap.xml')
        logger.info(f"Fetching sitemap from: {sitemap_url}")

        try:
            response = self.rate_limited_request(sitemap_url)
            response.raise_for_status()

            # Parse XML without namespace handling
            content = response.text
            # Remove namespace declarations for easier parsing
            content = re.sub(r'xmlns[^=]*="[^"]*"', '', content)
            content = re.sub(r'xmlns:[^=]*="[^"]*"', '', content)

            root = ET.fromstring(content.encode('utf-8'))

            urls = []

            # Check if it's a sitemap index
            if 'sitemapindex' in root.tag:
                # This is a sitemap index, fetch each sitemap
                for sitemap in root.findall('.//sitemap'):
                    loc = sitemap.find('./loc')
                    if loc is not None and loc.text:
                        sub_sitemap_url = loc.text.strip()
                        logger.info(f"Found sub-sitemap: {sub_sitemap_url}")
                        urls.extend(self.get_urls_from_sitemap(sub_sitemap_url))
            else:
                # Regular sitemap
                urls = self.get_urls_from_sitemap(sitemap_url)

            # Since the sitemap shows openwebui.com URLs, let's check if we should use those
            # or if there are actual docs.openwebui.com pages
            if not any('docs.openwebui.com' in url for url in urls):
                logger.info("Sitemap contains main site URLs. Checking docs subdomain...")
                # Let's crawl from the docs homepage instead
                return self.crawl_from_homepage()

            # Filter for documentation pages only
            doc_urls = [url for url in urls if self.is_doc_url(url)]

            logger.info(f"Found {len(doc_urls)} documentation URLs in sitemap")
            return doc_urls

        except Exception as e:
            logger.error(f"Error fetching sitemap: {e}")
            logger.info("Falling back to homepage crawling...")
            return self.crawl_from_homepage()

    def crawl_from_homepage(self):
        """Crawl URLs starting from the homepage"""
        logger.info("Starting crawl from homepage...")
        urls_to_process = [self.base_url]
        found_urls = set()
        processed = set()

        while urls_to_process and len(found_urls) < 500:  # Limit to prevent infinite crawling
            current_url = urls_to_process.pop(0)
            if current_url in processed:
                continue

            processed.add(current_url)

            try:
                if not self.can_fetch(current_url):
                    continue

                response = self.rate_limited_request(current_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find all links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    absolute_url = urljoin(current_url, href)
                    parsed = urlparse(absolute_url)

                    # Only follow links within the docs domain
                    if parsed.netloc == self.domain:
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            clean_url += f"?{parsed.query}"

                        if clean_url not in found_urls and self.is_doc_url(clean_url):
                            found_urls.add(clean_url)
                            if clean_url not in processed:
                                urls_to_process.append(clean_url)

            except Exception as e:
                logger.error(f"Error crawling {current_url}: {e}")

        logger.info(f"Found {len(found_urls)} URLs through crawling")
        return list(found_urls)

    def get_urls_from_sitemap(self, sitemap_url):
        """Extract URLs from a single sitemap"""
        try:
            response = self.rate_limited_request(sitemap_url)
            response.raise_for_status()

            # Remove namespaces for easier parsing
            content = response.text
            content = re.sub(r'xmlns[^=]*="[^"]*"', '', content)
            content = re.sub(r'xmlns:[^=]*="[^"]*"', '', content)

            root = ET.fromstring(content.encode('utf-8'))
            urls = []

            # Find all URL elements
            for url_elem in root.findall('.//url'):
                loc_elem = url_elem.find('./loc')
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())

            # If no urls found, try looking for loc tags directly
            if not urls:
                for loc_elem in root.findall('.//loc'):
                    if loc_elem.text:
                        urls.append(loc_elem.text.strip())

            return urls

        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
            return []

    def is_doc_url(self, url):
        """Check if URL is a documentation page"""
        # Skip non-HTML resources
        skip_extensions = ['.xml', '.pdf', '.zip', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.json', '.txt']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip certain patterns
        skip_patterns = ['/blog/', '/tag/', '/tags/', '/archive/', '/authors/']
        if any(pattern in url.lower() for pattern in skip_patterns):
            return False

        # Accept URLs from either docs.openwebui.com or openwebui.com
        parsed = urlparse(url)
        return parsed.netloc in [self.domain, 'openwebui.com', 'www.openwebui.com']

    def clean_content_for_rag(self, soup):
        """Clean and prepare content optimized for RAG"""
        # Remove all navigation, headers, footers, etc.
        selectors_to_remove = [
            'header', 'nav', 'footer', 'aside',
            '.navbar', '.footer', '.sidebar', '.navigation',
            '.theme-doc-sidebar-container',
            '.theme-doc-toc-desktop',
            '.theme-doc-breadcrumbs',
            '.pagination-nav',
            '.theme-doc-version-banner',
            '.theme-back-to-top-button',
            '[class*="sidebar"]',
            '[class*="navbar"]',
            '[class*="footer"]',
            'script', 'style', 'noscript',
            '.edit-this-page',
            '.theme-last-updated'
        ]

        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()

        # Remove all links but keep their text
        for link in soup.find_all('a'):
            link.replace_with(link.get_text())

        # Find main content
        main_content = (
                soup.find('article') or
                soup.find('main') or
                soup.find('div', {'class': 'theme-doc-markdown'}) or
                soup.find('div', {'class': 'markdown'}) or
                soup.find('div', {'class': 'container'})
        )

        if not main_content:
            main_content = soup.body

        # Remove empty divs and clean up
        if main_content:
            for div in main_content.find_all(['div', 'span']):
                if not div.get_text(strip=True):
                    div.decompose()

        return main_content

    def post_process_markdown(self, markdown_text):
        """Post-process markdown for better RAG performance"""
        # Remove multiple consecutive newlines
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in markdown_text.split('\n')]
        markdown_text = '\n'.join(lines)

        # Remove empty headers
        markdown_text = re.sub(r'^#{1,6}\s*$', '', markdown_text, flags=re.MULTILINE)

        # Remove standalone links (leftover from link removal)
        markdown_text = re.sub(r'^\s*https?://\S+\s*$', '', markdown_text, flags=re.MULTILINE)

        # Clean up excessive whitespace again
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        # Remove any remaining HTML comments except our URL comment
        markdown_text = re.sub(r'<!--(?!.*https://).*?-->', '', markdown_text, flags=re.DOTALL)

        return markdown_text.strip()

    def url_to_filename(self, url):
        """Convert URL to a safe filename"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if not path:
            path = "index"

        # Create more readable filenames
        filename = path.replace('/', '_')

        # Remove trailing slashes and clean up
        filename = filename.strip('_')

        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'

        return filename

    def extract_title(self, soup, url):
        """Extract the most relevant title for the page"""
        # Try to find the main heading
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        # Try page title
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            # Remove common suffixes
            title_text = re.sub(r'\s*[\||\-]\s*Open ?WebUI.*$', '', title_text, re.IGNORECASE)
            return title_text

        # Fallback to URL path
        path = urlparse(url).path.strip('/')
        if path:
            return path.replace('-', ' ').replace('_', ' ').title()

        return 'Documentation Page'

    def scrape_page(self, url):
        """Scrape a single page and convert to RAG-optimized markdown"""
        try:
            if not self.can_fetch(url):
                logger.warning(f"Robots.txt disallows: {url}")
                return False

            logger.info(f"Scraping: {url}")
            response = self.rate_limited_request(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title before cleaning
            title = self.extract_title(soup, url)

            # Clean the content for RAG
            clean_soup = self.clean_content_for_rag(soup)

            if not clean_soup:
                logger.warning(f"No content found for {url}")
                return False

            # Convert to markdown with custom settings
            markdown_content = markdownify.markdownify(
                str(clean_soup),
                heading_style="ATX",
                bullets="-",
                code_language="",  # Don't assume language
                strip=['a']  # Strip link tags
            )

            # Post-process the markdown
            markdown_content = self.post_process_markdown(markdown_content)

            if not markdown_content.strip():
                logger.warning(f"Empty content after processing for {url}")
                return False

            # Save to file
            filename = self.url_to_filename(url)
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                # Add URL as HTML comment for reference
                # f.write(f"<!-- {url} -->\n\n")  # NO!

                # Add title as main header
                f.write(f"# {title}\n\n")

                # Add the content
                f.write(markdown_content)

            logger.info(f"✓ Saved: {filename}")
            return True

        except Exception as e:
            logger.error(f"✗ Error scraping {url}: {str(e)}")
            return False

    def crawl(self):
        """Start the crawling process"""
        logger.info("=" * 60)
        logger.info("Starting RAG-optimized crawl")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

        # Get all URLs (either from sitemap or crawling)
        all_urls = self.get_sitemap_urls()

        if not all_urls:
            logger.error("No URLs found!")
            return

        logger.info(f"Found {len(all_urls)} URLs to scrape")

        # Process URLs with thread pool
        successful = 0
        failed = 0
        scraped_files = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {executor.submit(self.scrape_page, url): url for url in all_urls}

            # Process completed tasks
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success = future.result()
                    if success:
                        successful += 1
                        filename = self.url_to_filename(url)
                        scraped_files.append(filename)
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Exception for {url}: {e}")
                    failed += 1

                # Progress update
                total_processed = successful + failed
                if total_processed % 10 == 0:
                    logger.info(f"Progress: {total_processed}/{len(all_urls)} pages processed")

        # Final summary
        logger.info("=" * 60)
        logger.info("RAG-optimized crawling complete!")
        logger.info(f"✓ Successfully scraped: {successful} pages")
        logger.info(f"✗ Failed: {failed} pages")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)


def main():
    # Configuration
    START_URL = "https://docs.openwebui.com/"
    OUTPUT_DIR = "openwebui_rag_docs"
    REQUEST_DELAY = 1.0  # 1 second between requests
    MAX_WORKERS = 3  # 3 concurrent workers

    # Create and run scraper
    scraper = RAGOptimizedScraper(
        base_url=START_URL,
        output_dir=OUTPUT_DIR,
        delay=REQUEST_DELAY,
        max_workers=MAX_WORKERS
    )

    scraper.crawl()


if __name__ == "__main__":
    main()
