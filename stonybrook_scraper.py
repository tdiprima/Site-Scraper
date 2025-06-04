"""
stonybrook_scraper.py

Crawls the Stony Brook University website, starting from the homepage.
- Visits each unique internal HTML page once.
- Extracts and cleans main content (removes nav, headers, footers).
- Saves content as Markdown files in an output directory.
- Skips broken or slow pages without retrying.
- Saves crawling progress so you can resume later if interrupted.

Dependencies: crawl4ai, BeautifulSoup4
"""
import asyncio
import os
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy


async def clean_content(content, url):
    soup = BeautifulSoup(content, 'html.parser')

    # Remove headers, footers, and navigation
    for element in soup.find_all(['header', 'footer', 'nav']):
        element.decompose()

    # Try multiple selectors for main content
    main_content = None
    selectors = ['main', 'div[role="main"]', 'div.region-content', 'article', 'div#content']
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
            instruction="Extract the main textual content from the webpage, ignoring headers, footers, and navigation elements.")

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
                # Just try ONCE per page
                result = await crawler.arun(url=url, extraction_strategy=extraction_strategy, bypass_cache=True,
                    obey_robots=True)

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
                        if any(ext in path for ext in
                               ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg']):
                            continue

                        # Only queue links within allowed domain
                        if parsed_href.netloc == allowed_domain and href not in visited and href not in queue:
                            queue.append(href)

                else:
                    print(f"⚠️ Extraction failed for {url}. Reason: {getattr(result, 'error', 'Unknown error')}")
            except Exception as e:
                print(f"⏩ Skipping {url} due to error: {str(e)}")  # Move on to next URL. No retry.

            # Save queue (every time, in case of crash)
            with open(queue_file, 'w', encoding='utf-8') as f:
                for item in queue:
                    f.write(item + "\n")

            await asyncio.sleep(1.5)  # <- throttle requests


if __name__ == "__main__":
    try:
        asyncio.run(crawl_website())
    except KeyboardInterrupt:
        print("\n🛑 Crawl interrupted. Queue and visited URLs saved.")
    except Exception as e:
        print(f"\n🔥 Fatal error in crawl: {e}")
    print("👋 Done!")
