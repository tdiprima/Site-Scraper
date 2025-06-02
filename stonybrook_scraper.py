import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import os
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

async def clean_content(content, url):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Remove headers, footers, and navigation
    for element in soup.find_all(['header', 'footer', 'nav']):
        element.decompose()
    
    # Try multiple selectors for main content
    main_content = None
    selectors = [
        'main',
        'div[role="main"]',
        'div.region-content',  # Match your script's selector
        'article',
        'div#content'
    ]
    for selector in selectors:
        main_content = soup.find(selector)
        if main_content:
            break
    
    if not main_content:
        main_content = soup.find('body')  # Fallback to body if no main content found
    
    if main_content:
        # Remove script and style elements
        for element in main_content.find_all(['script', 'style']):
            element.decompose()
        
        # Get text, preserving basic formatting
        text = main_content.get_text(separator='\n', strip=True)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    return ""

async def crawl_website():
    async with AsyncWebCrawler() as crawler:
        # Configure extraction strategy
        extraction_strategy = LLMExtractionStrategy(
            instruction="Extract the main textual content from the webpage, ignoring headers, footers, and navigation elements."
        )
        
        # Set up output directory and tracking files
        output_dir = "stonybrook_content"
        visited_file = "visited.txt"
        queue_file = "queue.txt"
        os.makedirs(output_dir, exist_ok=True)
        
        # Load visited URLs
        visited = set()
        if os.path.exists(visited_file):
            with open(visited_file, 'r', encoding='utf-8') as f:
                visited = set(line.strip() for line in f if line.strip())
        
        # Load or initialize queue
        queue = [f"https://www.stonybrook.edu/"]
        if os.path.exists(queue_file):
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue = [line.strip() for line in f if line.strip()]
        
        allowed_extensions = ['.html', '.htm', '']
        allowed_domain = "www.stonybrook.edu"
        
        while queue:
            url = queue.pop(0)
            if url in visited:
                continue
                
            visited.add(url)
            
            # Save visited URL
            with open(visited_file, 'a', encoding='utf-8') as f:
                f.write(url + "\n")
            
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
                        parsed = urlparse(url)
                        path = parsed.path.strip("/").replace("/", "_") or "index"
                        filename = f"{parsed.netloc.replace('.', '_')}_{path}.md"
                        filepath = os.path.join(output_dir, filename)
                        
                        # Write to markdown file
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(cleaned_content)
                        
                        print(f"✅ Saved {url} → {filepath}")
                    
                    # Enqueue internal links
                    soup = BeautifulSoup(result.html, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = urljoin(url, link['href'])
                        parsed_href = urlparse(href)
                        path = parsed_href.path.lower()
                        
                        # Skip unwanted extensions
                        if any(ext in path for ext in ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg']):
                            continue
                            
                        # Only queue links within allowed domain
                        if parsed_href.netloc == allowed_domain and href not in visited and href not in queue:
                            queue.append(href)
                            
            except Exception as e:
                print(f"⚠️ Error processing {url}: {str(e)}")
            
            # Save queue
            with open(queue_file, 'w', encoding='utf-8') as f:
                for item in queue:
                    f.write(item + "\n")
                    
if __name__ == "__main__":
    try:
        asyncio.run(crawl_website())
    except KeyboardInterrupt:
        print("\n🛑 Crawl interrupted. Queue and visited URLs saved.")
    print("👋 Done!")
