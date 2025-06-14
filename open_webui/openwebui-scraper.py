import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import markdownify
from queue import Queue
from threading import Thread, Lock
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocsScraper:
    def __init__(self, base_url, output_dir="scraped_docs", max_depth=3, 
                 delay=1.0, max_workers=3):
        """
        Initialize the scraper.
        
        Args:
            base_url: Starting URL
            output_dir: Directory to save markdown files
            max_depth: Maximum crawl depth (3 levels from start URL)
            delay: Delay between requests in seconds
            max_workers: Number of worker threads (kept low to be server-friendly)
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.delay = delay
        self.max_workers = max_workers
        
        # Thread-safe structures
        self.visited_urls = set()
        self.url_queue = Queue()
        self.lock = Lock()
        self.last_request_time = 0
        self.request_lock = Lock()
        
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
            logger.info(f"Successfully loaded robots.txt from {robots_url}")
        except:
            logger.warning(f"Could not load robots.txt from {robots_url}")
            
    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        return self.robot_parser.can_fetch("*", url)
    
    def rate_limited_request(self, url):
        """Make a rate-limited request to be kind to the server"""
        with self.request_lock:
            # Calculate time to wait
            elapsed = time.time() - self.last_request_time
            if elapsed < self.delay:
                sleep_time = self.delay - elapsed
                logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Make request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Compatible; DocsScraper/1.0; Educational Purpose)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            self.last_request_time = time.time()
            
            return response
    
    def clean_content(self, soup):
        """Remove headers, sidebars, footers, and navigation elements"""
        # Common selectors for elements to remove
        selectors_to_remove = [
            'header', 'nav', 'footer', 'aside',
            '.header', '.nav', '.navbar', '.footer', '.sidebar',
            '.navigation', '.menu', '.breadcrumb',
            '#header', '#nav', '#navbar', '#footer', '#sidebar',
            '[role="navigation"]', '[role="banner"]', 
            '[role="contentinfo"]', '[role="complementary"]'
        ]
        
        for selector in selectors_to_remove:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', {'class': 'content'}) or
            soup.find('div', {'id': 'content'}) or
            soup.find('div', {'role': 'main'})
        )
        
        return main_content if main_content else soup.body
    
    def extract_links(self, soup, current_url, current_depth):
        """Extract valid links from the page"""
        links = []
        
        if current_depth >= self.max_depth:
            return links
            
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(current_url, href)
            parsed = urlparse(absolute_url)
            
            # Only follow links within the same domain
            if parsed.netloc == self.domain:
                # Remove fragment and normalize
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    clean_url += f"?{parsed.query}"
                    
                links.append((clean_url, current_depth + 1))
                
        return links
    
    def url_to_filename(self, url):
        """Convert URL to a safe filename"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            path = "index"
        
        # Replace slashes with underscores
        filename = path.replace('/', '_')
        
        # Add query parameters if any
        if parsed.query:
            query = parsed.query.replace('&', '_').replace('=', '_')
            filename += f"_{query}"
            
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
            
        return filename
    
    def scrape_page(self, url, depth):
        """Scrape a single page and convert to markdown"""
        try:
            if not self.can_fetch(url):
                logger.warning(f"Robots.txt disallows: {url}")
                return []
            
            logger.info(f"Scraping: {url} (depth: {depth})")
            response = self.rate_limited_request(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Clean the content
            clean_soup = self.clean_content(soup)
            
            # Convert to markdown
            markdown_content = markdownify.markdownify(
                str(clean_soup),
                heading_style="ATX",
                bullets="-",
                code_language="python"
            )
            
            # Save to file
            filename = self.url_to_filename(url)
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# Source: {url}\n")
                f.write(f"# Scraped: {datetime.now().isoformat()}\n")
                f.write(f"# Depth: {depth}\n\n")
                f.write(markdown_content)
            
            logger.info(f"Saved: {filepath}")
            
            # Extract links for further crawling
            links = self.extract_links(soup, url, depth)
            return links
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []
    
    def worker(self):
        """Worker thread function"""
        while True:
            try:
                url, depth = self.url_queue.get(timeout=5)
                
                # Check if already visited
                with self.lock:
                    if url in self.visited_urls:
                        self.url_queue.task_done()
                        continue
                    self.visited_urls.add(url)
                
                # Scrape the page
                new_links = self.scrape_page(url, depth)
                
                # Add new links to queue
                with self.lock:
                    for link_url, link_depth in new_links:
                        if link_url not in self.visited_urls:
                            self.url_queue.put((link_url, link_depth))
                
                self.url_queue.task_done()
                
            except:
                break
    
    def crawl(self):
        """Start the crawling process"""
        logger.info(f"Starting crawl of {self.base_url}")
        logger.info(f"Max depth: {self.max_depth}, Workers: {self.max_workers}")
        
        # Add starting URL to queue
        self.url_queue.put((self.base_url, 0))
        
        # Start worker threads
        threads = []
        for i in range(self.max_workers):
            t = Thread(target=self.worker, name=f"Worker-{i+1}")
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Wait for all URLs to be processed
        self.url_queue.join()
        
        logger.info(f"Crawling complete! Scraped {len(self.visited_urls)} pages")
        logger.info(f"Files saved to: {self.output_dir}")


def main():
    # Configuration
    START_URL = "https://docs.openwebui.com/"
    OUTPUT_DIR = "openwebui_docs"
    MAX_DEPTH = 3  # 3 levels deep from the start URL
    REQUEST_DELAY = 1.5  # 1.5 seconds between requests (being extra kind)
    MAX_WORKERS = 3  # Only 3 concurrent workers (well below your 8 cores)
    
    # Create and run scraper
    scraper = DocsScraper(
        base_url=START_URL,
        output_dir=OUTPUT_DIR,
        max_depth=MAX_DEPTH,
        delay=REQUEST_DELAY,
        max_workers=MAX_WORKERS
    )
    
    scraper.crawl()


if __name__ == "__main__":
    main()
