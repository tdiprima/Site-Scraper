import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re

async def clean_content(content, url):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove headers and footers
    for element in soup.find_all(['header', 'footer', 'nav']):
        element.decompose()
    
    # Extract main content
    main_content = ''
    main_tag = soup.find('main') or soup.find('div', {'role': 'main'}) or soup.find('body')
    if main_tag:
        # Remove script and style elements
        for element in main_tag.find_all(['script', 'style']):
            element.decompose()
        
        # Get text, preserving some basic formatting
        text = main_tag.get_text(separator='\n', strip=True)
        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        main_content = text.strip()
    
    return main_content

async def crawl_website():
    async with AsyncWebCrawler() as crawler:
        # Configure extraction strategy
        extraction_strategy = LLMExtractionStrategy(
            instruction="Extract the main textual content from the webpage, ignoring headers, footers, and navigation elements."
        )
        
        # Set up output directory
        output_dir = "stonybrook_content"
        os.makedirs(output_dir, exist_ok=True)
        
        # Crawl parameters
        start_url = "https://www.stonybrook.edu/"
        visited_urls = set()
        allowed_extensions = ['.html', '.htm', '']
        
        async def process_url(url, depth=0, max_depth=2):
            if depth > max_depth:
                return
            
            # Check if URL has valid extension
            if not any(url.lower().endswith(ext) for ext in allowed_extensions):
                return
                
            if url in visited_urls:
                return
                
            visited_urls.add(url)
            
            try:
                result = await crawler.arun(
                    url=url,
                    extraction_strategy=extraction_strategy,
                    bypass_cache=True,
                    obey_robots=True
                )
                
                if result.success:
                    # Clean and process content
                    cleaned_content = await clean_content(result.html, url)
                    
                    if cleaned_content:
                        # Create safe filename from URL
                        filename = re.sub(r'[^\w\-_\.]', '_', url.split('/')[-1] or 'index')
                        if not filename.endswith('.md'):
                            filename += '.md'
                            
                        # Write to markdown file
                        filepath = os.path.join(output_dir, filename)
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(f"# Content from {url}\n\n")
                            f.write(cleaned_content)
                        
                        # Find and process linked URLs
                        soup = BeautifulSoup(result.html, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            absolute_url = urljoin(url, href)
                            if absolute_url.startswith(start_url):
                                await process_url(absolute_url, depth + 1, max_depth)
                                
            except Exception as e:
                print(f"Error processing {url}: {str(e)}")
                
        await process_url(start_url)

if __name__ == "__main__":
    asyncio.run(crawl_website())
    print("✅ Done!")
