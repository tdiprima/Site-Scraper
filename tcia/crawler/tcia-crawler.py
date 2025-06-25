#!/usr/bin/env python3
"""
Web crawler for The Cancer Imaging Archive website
Respects robots.txt, uses multiprocessing, and saves as markdown files
"""

import os
import sys
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
    level=logging.INFO,
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
        except Exception as e:
            logger.warning(f"Could not read robots.txt: {e}")
        
        # Create output directory
        self.output_dir = 'tcia_scrape_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True  # This will convert links to just their text
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
            return False
            
        # Check file extension
        path = parsed.path.lower()
        if any(path.endswith(ext) for ext in self.skip_extensions):
            return False
            
        # Check robots.txt
        try:
            if self.robot_parser and not self.robot_parser.can_fetch('*', url):
                logger.debug(f"Robots.txt disallows: {url}")
                return False
        except:
            # If robots.txt check fails, allow the URL
            pass
            
        return True
    
    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
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
            soup_copy.find('div', {'class': 'wrapper'}),
            soup_copy.find('div', {'class': 'page-content'}),
            soup_copy.find('div', {'id': 'page-content'})
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
                try:
                    for element in main_content.select(selector):
                        element.decompose()
                except:
                    pass
        
        return main_content
    
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
        
        # Write markdown content (without URL header)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return None
    
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
            
            # Find all links BEFORE removing content
            found_urls = set()
            all_links = full_soup.find_all('a', href=True)
            logger.debug(f"Total links found on page: {len(all_links)}")
            
            for link in all_links:
                href = link['href']
                link_text = link.get_text(strip=True)
                
                # Skip javascript links, mailto, tel, etc
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                
                # Skip empty hrefs
                if not href or href == '#':
                    continue
                    
                absolute_url = urljoin(url, href)
                absolute_url = absolute_url.split('#')[0]  # Remove anchors
                
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited:
                    found_urls.add(absolute_url)
                    logger.debug(f"Found valid link: {absolute_url} (text: {link_text})")
            
            # Extract main content for saving
            main_content = self.extract_main_content(full_soup)
            
            # Convert to markdown (html2text will handle link text extraction)
            if main_content:
                markdown_content = self.h2t.handle(str(main_content))
            else:
                markdown_content = "No content found"
            
            # Save to file
            filepath = self.save_as_markdown(url, markdown_content)
            if filepath:
                logger.info(f"Saved: {filepath}")
            logger.info(f"Found {len(found_urls)} new URLs to crawl")
            
            return found_urls
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return set()
    
    def crawl(self):
        """Main crawling function"""
        # Start with homepage and browse-collections
        initial_urls = [
            self.base_url,
            urljoin(self.base_url, "/browse-collections/")
        ]
        
        # Queue of (url, depth) tuples
        to_visit = deque()
        
        # Add initial URLs
        for url in initial_urls:
            to_visit.append((url, 0))
            self.visited.add(url)
        
        # Sequential crawling for better debugging
        while to_visit:
            url, depth = to_visit.popleft()
            
            if depth <= self.max_depth:
                found_urls = self.scrape_page(url, depth)
                
                # Add new URLs to queue
                for new_url in found_urls:
                    if new_url not in self.visited:
                        to_visit.append((new_url, depth + 1))
                        self.visited.add(new_url)
                        
            # Show progress
            if len(self.visited) % 10 == 0:
                logger.info(f"Progress: {len(self.visited)} URLs visited, {len(to_visit)} in queue")
        
        logger.info(f"Crawling complete. Scraped {len(self.visited)} pages.")
        
        # List files created
        files = os.listdir(self.output_dir)
        logger.info(f"Created {len(files)} markdown files")


def main():
    """Main function"""
    # Test connection first
    test_url = "https://www.cancerimagingarchive.net/"
    logger.info(f"Testing connection to {test_url}")
    
    try:
        response = requests.get(test_url, timeout=10)
        logger.info(f"Connection successful, status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        sys.exit(1)
    
    crawler = TCIACrawler(
        base_url="https://www.cancerimagingarchive.net/",
        max_workers=16,  # Not used in sequential version
        max_depth=5      # Limiting to 3 levels deep
    )
    
    logger.info(f"Starting crawl of {crawler.base_url}")
    logger.info(f"Max depth: {crawler.max_depth}")
    logger.info(f"Output directory: {crawler.output_dir}")
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
