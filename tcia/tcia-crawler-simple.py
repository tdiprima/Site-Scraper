#!/usr/bin/env python3
"""
Simple sequential web crawler for The Cancer Imaging Archive website
Saves pages as markdown files without URLs
"""

import os
import time
import hashlib
from urllib.parse import urljoin, urlparse
from collections import deque
import requests
from bs4 import BeautifulSoup
import html2text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TCIACrawler:
    def __init__(self, base_url: str, max_depth: int = 3):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Extensions to skip
        self.skip_extensions = {
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', 
            '.xls', '.xlsx', '.png', '.jpg', '.jpeg',
            '.gif', '.bmp', '.svg', '.ico', '.webp',
            '.mp4', '.mp3', '.avi', '.mov', '.zip',
            '.tar', '.gz', '.rar', '.exe', '.dmg',
            '.json', '.xml', '.csv'
        }
        
        # Create output directory
        self.output_dir = 'tcia_scrape_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # HTML to Markdown converter
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = True  # Convert links to just their text
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
            
        return True
    
    def extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content as text"""
        # Remove script and style elements
        for tag in soup(['script', 'style', 'header', 'nav', 'footer']):
            tag.decompose()
            
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', {'class': 'content'}) or
            soup.find('div', {'class': 'container'}) or
            soup.body
        )
        
        if main_content:
            # Convert to markdown
            return self.h2t.handle(str(main_content))
        else:
            return "No content found"
    
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
            logger.info(f"Scraping: {url}")
            
            # Add delay to be polite
            time.sleep(1)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
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
            content = self.extract_main_content(soup)
            filepath = self.save_as_markdown(url, content)
            
            if filepath:
                logger.info(f"Saved: {os.path.basename(filepath)}")
            
            return found_urls
            
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
        while queue:
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
    logger.info("Starting TCIA crawler")
    
    crawler = TCIACrawler(
        base_url="https://www.cancerimagingarchive.net/",
        max_depth=2  # Start with depth 2 to see if we get collections
    )
    
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        logger.info("Crawling interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
