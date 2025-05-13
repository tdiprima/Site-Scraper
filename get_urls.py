import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

async def main():
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=2, max_pages=50),
        )
        results = await crawler.arun(url="https://bmi.stonybrookmedicine.edu", config=config)
        for result in results:
            print(result.url)

if __name__ == "__main__":
    asyncio.run(main())

