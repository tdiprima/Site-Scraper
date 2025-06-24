#!/usr/bin/env python3
"""
Web crawler for The Cancer Imaging Archive website
Respects robots.txt, uses multiprocessing, and saves as markdown files
Enhanced version with better debugging and dynamic content handling
"""

import os
import time
import hashlib
from urllib.parse import urljoin, urlparse, unquote
from urllib.robotparser import RobotFileParser
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import deque
import requests
from bs4 import BeautifulSoup
import html2text
import logging
from typing import Set, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCIACrawler:
    def __init__(self, base_url: str, max_workers: int = 16, max_depth: int = 3):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_workers = max_workers
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Extensions to skip
        self.skip_extensions = {
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
            '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
            '.gif', '.bmp', '.svg', '.ico', '.webp',
            '.mp4', '.mp3', '.avi', '.mov', '.zip',
            '.tar', '.gz', '.rar', '.exe', '.dmg'
        }
        
        # Setup robots.txt parser
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(base_url, '/robots.txt'))
        try:
            self.robot_parser.read()
            logger.info("Successfully read robots.txt")
        except:
            logger.warning("Could not read robots.txt, proceeding with caution")
        
        # Create output directory
        self.output_dir = 'tcia_scrape_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0  # Don't wrap lines
        
        # Track visited URLs
        self.visited = set()
        
    def is_valid_url(self, url: str) -> bool:
        """Check if URL should be crawled"""
        # Remove fragment
        url = url.split('#')[0]
        
        # Check if it's within our domain
        parsed = urlparse(url)
        if parsed.netloc != self.domain:
            logger.debug(f"Skipping external URL: {url}")
            return False
            
        # Check file extension
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in self.skip_extensions):
            logger.debug(f"Skipping file extension: {url}")
            return False
            
        # Check robots.txt
        if not self.robot_parser.can_fetch('*', url):
            logger.debug(f"Robots.txt disallows: {url}")
            return False
            
        return True
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content, ignoring headers and footers"""
        # Make a copy to preserve original
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        
        # Remove script and style elements
        for tag in soup_copy(['script', 'style']):
            tag.decompose()
            
        # Try multiple strategies to find content
        main_content = None
        
        # Strategy 1: Look for main content containers
        content_candidates = [
            soup_copy.find('main'),
            soup_copy.find('article'),
            soup_copy.find('div', {'class': 'content'}),
            soup_copy.find('div', {'id': 'content'}),
            soup_copy.find('div', {'role': 'main'}),
            soup_copy.find('div', {'class': 'container'}),
            soup_copy.find('div', {'class': 'wrapper'})
        ]
        
        for candidate in content_candidates:
            if candidate:
                main_content = candidate
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup_copy.body or soup_copy
            
        # Remove navigation elements after finding main content
        if main_content:
            for tag in main_content.find_all(['header', 'nav', 'footer', 'aside']):
                tag.decompose()
                
            # Remove elements with common navigation classes/ids
            nav_selectors = [
                '[class*="navbar"]', '[class*="header"]', '[class*="footer"]', 
                '[class*="navigation"]', '[class*="menu"]', '[id*="header"]', 
                '[id*="footer"]', '[id*="navigation"]', '[id*="menu"]', 
                '.breadcrumb', '[class*="sidebar"]'
            ]
            
            for selector in nav_selectors:
                for element in main_content.select(selector):
                    element.decompose()
        
        # Convert links to just text (remove href) but keep the structure
        for link in main_content.find_all('a'):
            link_text = link.get_text(strip=True)
            if link_text:
                link.string = link_text
            else:
                link.decompose()
                
        return str(main_content)
    
    def save_as_markdown(self, url: str, content: str) -> str:
        """Save content as markdown file"""
        # Create filename from URL
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if not path or path == '/':
            filename = 'index.md'
        else:
            # Replace slashes with underscores
            filename = path.replace('/', '_') + '.md'
            
        # Ensure filename is valid
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        
        # Add hash if filename already exists
        filepath = os.path.join(self.output_dir, filename)
        if os.path.exists(filepath):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{filename.rsplit('.', 1)[0]}_{url_hash}.md"
            filepath = os.path.join(self.output_dir, filename)
        
        # Write markdown content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {url}\n\n")
            f.write(content)
            
        return filepath
    
    def scrape_page(self, url: str, depth: int) -> Set[str]:
        """Scrape a single page and return found URLs"""
        if depth > self.max_depth:
            return set()
            
        try:
            logger.info(f"Scraping: {url} (depth: {depth})")
            
            # Add delay to be polite
            time.sleep(0.5)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the full page to find links
            full_soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: print all links found
            all_links = full_soup.find_all('a', href=True)
            logger.debug(f"Total links found on page: {len(all_links)}")
            
            # Find all links BEFORE removing content
            found_urls = set()
            for link in all_links:
                href = link['href']
                link_text = link.get_text(strip=True)
                
                # Skip javascript links, mailto, tel, etc
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    logger.debug(f"Skipping special link: {href}")
                    continue
                
                # Skip empty hrefs
                if not href or href == '#':
                    continue
                    
                absolute_url = urljoin(url, href)
                absolute_url = absolute_url.split('#')[0]  # Remove anchors
                
                logger.debug(f"Checking link: {href} -> {absolute_url} (text: {link_text})")
                
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                    found_urls.add(absolute_url)
                    logger.info(f"Found valid link: {absolute_url}")
            
            # Extract main content for saving
            main_content = self.extract_main_content(full_soup)
            
            # Convert to markdown
            markdown_content = self.h2t.handle(main_content)
            
            # Save to file
            filepath = self.save_as_markdown(url, markdown_content)
            logger.info(f"Saved: {filepath}")
            logger.info(f"Found {len(found_urls)} new URLs to crawl")
            
            return found_urls
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}", exc_info=True)
            return set()
    
    def crawl(self):
        """Main crawling function using multiprocessing"""
        # First, scrape the initial page in the main process to debug
        logger.info("Starting with initial page scrape...")
        initial_urls = self.scrape_page(self.base_url, 0)
        logger.info(f"Initial page returned {len(initial_urls)} URLs")
        
        # Queue of (url, depth) tuples
        to_visit = deque()
        for url in initial_urls:
            to_visit.append((url, 1))
        
        self.visited.add(self.base_url)
        
        # If no URLs found, try to understand why
        if not initial_urls:
            logger.warning("No URLs found on initial page!")
            logger.info("Checking if page has any content...")
            
            # Do a simple request to see what we get
            resp = self.session.get(self.base_url)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Log some diagnostic info
            logger.debug(f"Page title: {soup.title.string if soup.title else 'No title'}")
            logger.debug(f"Number of divs: {len(soup.find_all('div'))}")
            logger.debug(f"Number of links: {len(soup.find_all('a'))}")
            
            # Print first few links for debugging
            for i, link in enumerate(soup.find_all('a', href=True)[:10]):
                logger.debug(f"Sample link {i}: href='{link.get('href')}' text='{link.get_text(strip=True)}'")
        
        # Continue with multiprocessing if we have URLs
        if to_visit:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                
                while to_visit or futures:
                    # Submit new tasks
                    while to_visit and len(futures) < self.max_workers:
                        url, depth = to_visit.popleft()
                        if url not in self.visited:
                            self.visited.add(url)
                            future = executor.submit(self.scrape_page, url, depth)
                            futures[future] = (url, depth)
                    
                    # Process completed tasks
                    if futures:
                        done, pending = as_completed(futures), set()
                        for future in done:
                            url, depth = futures.pop(future)
                            try:
                                found_urls = future.result()
                                # Add new URLs to queue
                                for new_url in found_urls:
                                    if new_url not in self.visited and depth < self.max_depth:
                                        to_visit.append((new_url, depth + 1))
                                        self.visited.add(new_url)
                            except Exception as e:
                                logger.error(f"Error processing result for {url}: {str(e)}")
                        
                        # Update futures with pending tasks
                        futures = {f: futures[f] for f in pending if f in futures}
                    
                    # Brief pause to prevent overwhelming the server
                    if futures:
                        time.sleep(0.1)
        
        logger.info(f"Crawling complete. Scraped {len(self.visited)} pages.")


def main():
    """Main function"""
    # Test with a simple request first
    logger.info("Testing connection to the website...")
    test_response = requests.get("https://www.cancerimagingarchive.net/", 
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    logger.info(f"Test response status: {test_response.status_code}")
    
    crawler = TCIACrawler(
        base_url="https://www.cancerimagingarchive.net/",
        max_workers=16,  # Using 16 workers to be polite to the server
        max_depth=3      # Limiting to 3 levels deep
    )
    
    logger.info(f"Starting crawl of {crawler.base_url}")
    logger.info(f"Using {crawler.max_workers} workers")
    logger.info(f"Max depth: {crawler.max_depth}")
    logger.info(f"Output directory: {crawler.output_dir}")
    logger.info(f"Robots.txt allows crawling: {crawler.robot_parser.can_fetch('*', crawler.base_url)}")
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
