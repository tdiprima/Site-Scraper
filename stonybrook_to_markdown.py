import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, FilterChain
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy


# Output directory for markdown files
OUTPUT_DIR = "bmi_stonybrook_markdown"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def save_markdown(url, markdown, page_num):
    """Save markdown content to a file."""
    # Sanitize URL to create a valid filename
    filename = url.replace("https://", "").replace("/", "_").replace(".", "_") + f"_page_{page_num}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Saved markdown for {url} to {filepath}")

async def main():
    # Configure browser (headless for efficiency)
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )

    # Configure crawler with deep crawling
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,  # Limit depth to avoid going too far
            max_pages=50,  # Stop after 50 pages
            filter_chain=FilterChain()  # Use default filter chain
        ),
        cache_mode="BYPASS",  # Ensure fresh content
        check_robots_txt=True  # Respect robots.txt
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Start crawling
        results = await crawler.arun(
            url="https://bmi.stonybrookmedicine.edu",
            config=run_config
        )

        # Save markdown for each crawled page
        for idx, result in enumerate(results):
            if result.success and result.markdown:
                await save_markdown(result.url, result.markdown.raw_markdown, idx + 1)
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
