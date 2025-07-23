#!/usr/bin/env python3
"""
Interfolio Documentation Scraper for RAG Server
Scrapes documentation from product-help.interfolio.com and saves as markdown files
"""

import os
import re
import time
import hashlib
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import requests
from markdownify import markdownify as md
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class InterfolioScraper:
    def __init__(self, base_url, output_dir="scraped_content", max_workers=8):
        self.base_url = base_url
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.visited_urls = set()
        self.failed_urls = set()
        self.domain = urlparse(base_url).netloc
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Chrome options for headless browsing
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        
    def get_driver(self):
        """Create and return a new Chrome driver instance"""
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            return driver
        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    def wait_for_content(self, driver, timeout=10):
        """Wait for JavaScript content to load"""
        try:
            # Wait for common content containers
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
            # Additional wait for dynamic content
            time.sleep(2)
        except TimeoutException:
            logger.warning("Timeout waiting for content to load")
    
    def extract_text_content(self, soup):
        """Extract text content from BeautifulSoup object, removing all links"""
        # Remove all anchor tags but keep their text
        for a in soup.find_all('a'):
            a.replace_with(a.get_text() or '')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def html_to_markdown(self, html_content):
        """Convert HTML to markdown, removing all links"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove navigation, headers, footers, etc.
        for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Remove common footer patterns
        for element in soup.find_all(text=re.compile(r'Was this article helpful\?', re.I)):
            parent = element.parent
            while parent and parent.name not in ['section', 'div', 'article']:
                parent = parent.parent
            if parent:
                parent.decompose()

        # Remove "Related Articles" sections
        for element in soup.find_all(text=re.compile(r'Related Articles', re.I)):
            parent = element.parent
            while parent and parent.name not in ['section', 'div', 'article']:
                parent = parent.parent
            if parent:
                parent.decompose()

        # Find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
        
        if not main_content:
            return ""
        
        # Remove all links but keep text
        for a in main_content.find_all('a'):
            a.replace_with(a.get_text() or '')
        
        # Convert to markdown
        markdown_content = md(str(main_content), heading_style="ATX", bullets="-")
        
        # Clean up excessive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        return markdown_content.strip()
    
    def generate_filename(self, url, title=None):
        """Generate a safe filename from URL and title"""
        path = urlparse(url).path
        if path.endswith('/'):
            path = path[:-1]
        
        if title:
            # Use title for filename
            filename = re.sub(r'[^\w\s-]', '', title.lower())
            filename = re.sub(r'[-\s]+', '-', filename)
        else:
            # Use URL path for filename
            filename = path.replace('/', '_')
            if not filename:
                filename = 'index'
        
        # Ensure unique filename
        base_filename = filename[:100]  # Limit length
        counter = 0
        while True:
            if counter == 0:
                full_filename = f"{base_filename}.md"
            else:
                full_filename = f"{base_filename}_{counter}.md"
            
            filepath = os.path.join(self.output_dir, full_filename)
            if not os.path.exists(filepath):
                return full_filename
            counter += 1
    
    def scrape_page(self, url):
        """Scrape a single page and save as markdown"""
        if url in self.visited_urls or url in self.failed_urls:
            return []
        
        logger.info(f"Scraping: {url}")
        self.visited_urls.add(url)
        
        driver = None
        try:
            driver = self.get_driver()
            driver.get(url)
            self.wait_for_content(driver)
            
            # Get page content
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text() if title else "Untitled"
            
            # Convert to markdown
            markdown_content = self.html_to_markdown(page_source)
            
            if markdown_content:
                # Save to file
                filename = self.generate_filename(url, title_text)
                filepath = os.path.join(self.output_dir, filename)
                
                # Add metadata
                # metadata = f"---\ntitle: {title_text}\nurl: {url}\nscraped_at: {datetime.now().isoformat()}\n---\n\n"
                metadata = f"title: {title_text}\n\n"

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(metadata + markdown_content)
                
                logger.info(f"Saved: {filename}")
            
            # Find internal links to scrape
            internal_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                parsed = urlparse(absolute_url)
                
                # Only follow internal links
                if parsed.netloc == self.domain and absolute_url not in self.visited_urls:
                    # Skip certain file types
                    if not any(absolute_url.endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip']):
                        internal_links.append(absolute_url)
            
            return list(set(internal_links))
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.failed_urls.add(url)
            return []
        finally:
            if driver:
                driver.quit()
    
    def scrape_site(self):
        """Scrape the entire site starting from base URL"""
        logger.info(f"Starting scrape of {self.base_url}")
        urls_to_scrape = [self.base_url]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while urls_to_scrape:
                # Submit batch of URLs for scraping
                futures = {executor.submit(self.scrape_page, url): url 
                          for url in urls_to_scrape[:self.max_workers]}
                urls_to_scrape = urls_to_scrape[self.max_workers:]
                
                # Process completed futures
                for future in as_completed(futures):
                    try:
                        new_urls = future.result()
                        # Add new URLs to queue
                        for url in new_urls:
                            if url not in self.visited_urls and url not in urls_to_scrape:
                                urls_to_scrape.append(url)
                    except Exception as e:
                        logger.error(f"Error processing future: {e}")
        
        logger.info(f"Scraping complete. Scraped {len(self.visited_urls)} pages.")
        logger.info(f"Failed URLs: {len(self.failed_urls)}")
        
        # Save failed URLs for reference
        if self.failed_urls:
            with open(os.path.join(self.output_dir, 'failed_urls.txt'), 'w') as f:
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
        logger.info(f"\nScraping completed!")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Total pages scraped: {len(scraper.visited_urls)}")
        logger.info(f"Failed pages: {len(scraper.failed_urls)}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
