#!/usr/bin/env python3
"""
Selenium-based web crawler for The Cancer Imaging Archive website
Handles JavaScript-rendered content

# Run in headless mode (no browser window)
python tcia-selenium-crawler.py --headless

# Or run with visible browser (for debugging)
python tcia-selenium-crawler.py
"""

import os
import time
import hashlib
from urllib.parse import urljoin, urlparse
from collections import deque
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import html2text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCIASeleniumCrawler:
    def __init__(self, base_url: str, max_depth: int = 3, headless: bool = True):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        
        # Extensions to skip
        self.skip_extensions = {
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
            '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
            '.gif', '.bmp', '.svg', '.ico', '.webp',
            '.mp4', '.mp3', '.avi', '.mov', '.zip',
            '.tar', '.gz', '.rar', '.exe', '.dmg',
            '.json', '.xml', '.csv'
        }
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Initialize driver
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            logger.info("Make sure you have Chrome and ChromeDriver installed")
            logger.info("Install with: sudo apt-get install chromium-chromedriver")
            raise
        
        # Create output directory - DIFFERENT from original to protect existing files
        self.output_dir = 'tcia_dynamic_content_only'
        os.makedirs(self.output_dir, exist_ok=True)
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
        
    def __del__(self):
        """Cleanup driver on exit"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        # Remove fragment
        url = url.split('#')[0]
        
        # Check if it's within our domain
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            return False
            
        # Check file extension
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in self.skip_extensions):
            return False
            
        return True
    
    def wait_for_content(self, timeout: int = 10):
        """Wait for dynamic content to load"""
        try:
            # Wait for body to be present
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for common content indicators
            content_selectors = [
                "main", "article", ".content", "#content", 
                ".container", "[role='main']", ".page-content"
            ]
            
            for selector in content_selectors:
                try:
                    WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            # Give JavaScript a bit more time to finish
            time.sleep(2)
            
        except TimeoutException:
            logger.warning("Timeout waiting for content to load")
    
    def check_if_dynamic_page(self, initial_html: str, final_html: str) -> bool:
        """Check if page content was loaded dynamically"""
        # Compare content length (dynamic pages usually have much more content after JS)
        initial_len = len(initial_html)
        final_len = len(final_html)
        
        # If content increased by more than 50%, likely dynamic
        if final_len > initial_len * 1.5:
            return True
            
        # Check for common signs of dynamic content
        initial_soup = BeautifulSoup(initial_html, 'html.parser')
        final_soup = BeautifulSoup(final_html, 'html.parser')
        
        # Count meaningful content elements
        initial_content = len(initial_soup.find_all(['p', 'div', 'article', 'section', 'main']))
        final_content = len(final_soup.find_all(['p', 'div', 'article', 'section', 'main']))
        
        # If content elements increased significantly, it's dynamic
        return final_content > initial_content * 1.3
    
    def extract_main_content(self, page_source: str) -> str:
        """Extract main content as text"""
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Remove script, style, and navigation elements FIRST
        for tag in soup(['script', 'style', 'header', 'nav', 'footer', 'aside', 'noscript']):
            tag.decompose()
            
        # Remove elements by class/id patterns
        nav_patterns = [
            '[class*="header"]', '[class*="footer"]', '[class*="navbar"]',
            '[class*="navigation"]', '[class*="menu"]', '[class*="sidebar"]',
            '[class*="breadcrumb"]', '[id*="header"]', '[id*="footer"]',
            '[id*="nav"]', '[id*="menu"]', '.top-bar', '.bottom-bar',
            '.site-header', '.site-footer', '.page-header', '.page-footer'
        ]
        
        for pattern in nav_patterns:
            for element in soup.select(pattern):
                element.decompose()
            
        # Try to find main content area
        main_content = None
        content_selectors = [
            'main', 'article', '.content', '#content',
            '.container', '[role="main"]', '.page-content',
            '.entry-content', '.post-content', 'section'
        ]
        
        for selector in content_selectors:
            if selector.startswith('.') or selector.startswith('#') or selector.startswith('['):
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
            return "No content found (even with Selenium)"
    
    def save_as_markdown(self, url: str, content: str) -> str:
        """Save content as markdown file"""
        # Create filename from URL
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path:
            filename = 'index.md'
        else:
            # Replace slashes with underscores
            filename = path.replace('/', '_') + '.md'
            
        # Clean filename
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        # Add hash if filename already exists
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{filename.rsplit('.', 1)[0]}_{url_hash}.md"
            filepath = os.path.join(self.output_dir, filename)
        
        # Write content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return None
    
    def scrape_page(self, url: str) -> set:
        """Scrape a single page and return found URLs"""
        try:
            logger.info(f"Checking: {url}")
            
            # First, get initial HTML without JavaScript
            import requests
            initial_response = requests.get(url, timeout=10)
            initial_html = initial_response.text
            
            # Load page with Selenium
            self.driver.get(url)
            
            # Wait for content to load
            self.wait_for_content()
            
            # Get page source after JavaScript execution
            final_html = self.driver.page_source
            
            # Check if this is a dynamic page
            if not self.check_if_dynamic_page(initial_html, final_html):
                logger.info(f"Skipping {url} - not dynamically loaded")
                # Still extract links for crawling
                soup = BeautifulSoup(final_html, 'html.parser')
                found_urls = set()
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if not href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                        absolute_url = urljoin(url, href).split('#')[0]
                        if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                            found_urls.add(absolute_url)
                return found_urls
            
            logger.info(f"Dynamic content detected - scraping: {url}")
            
            # Parse HTML
            soup = BeautifulSoup(final_html, 'html.parser')
            
            # Find all links
            found_urls = set()
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Skip non-http links
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                    
                # Convert to absolute URL
                absolute_url = urljoin(url, href)
                absolute_url = absolute_url.split('#')[0]  # Remove fragments
                
                # Check if valid and not visited
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                    found_urls.add(absolute_url)
            
            # Extract and save content
            content = self.extract_main_content(final_html)
            
            # Check if we got actual content
            if content and len(content.strip()) > 50:  # More than 50 chars
                filepath = self.save_as_markdown(url, content)
                if filepath:
                    logger.info(f"Saved: {os.path.basename(filepath)} ({len(content)} chars)")
            else:
                logger.warning(f"Little/no content found for {url}")
            
            return found_urls
            
        except WebDriverException as e:
            logger.error(f"WebDriver error scraping {url}: {e}")
            return set()
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return set()
    
    def crawl(self):
        """Main crawling function"""
        # Start with homepage and browse-collections
        start_urls = [
            self.base_url,
            urljoin(self.base_url, "/browse-collections/")
        ]
        
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
                logger.info(f"Progress: {processed} pages scraped, {len(queue)} in queue")
        
        # Final report
        files = os.listdir(self.output_dir)
        logger.info(f"Crawling complete!")
        logger.info(f"Pages scraped: {processed}")
        logger.info(f"Files created: {len(files)}")


def main():
    """Main function"""
    logger.info("Starting TCIA Selenium crawler")
    logger.info("This crawler handles JavaScript-rendered content")
    
    # Check if running in headless mode
    import sys
    headless = "--headless" not in sys.argv
    
    if not headless:
        logger.info("Running in headless mode (no browser window)")
    else:
        logger.info("Running with visible browser window")
    
    crawler = TCIASeleniumCrawler(
        base_url="https://www.cancerimagingarchive.net/",
        max_depth=2,  # Start with depth 2
        headless=headless
    )
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Ensure driver is closed
        if hasattr(crawler, 'driver'):
            crawler.driver.quit()


if __name__ == "__main__":
    main()
