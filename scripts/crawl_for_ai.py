"""
Keep browser visible and increase timeout because it wasn't working on MacOS.
"""
import asyncio

from crawl4ai import AsyncWebCrawler


async def main():
    # Initialize crawler with custom Playwright settings
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Configure crawler to run in headed mode and increase timeout
        result = await crawler.arun(
            url="https://bmi.stonybrookmedicine.edu",
            headless=False,  # Keep browser visible
            timeout=60000,  # 60-second timeout (in milliseconds)
            bypass_csp=True,  # Optional: bypass Content Security Policy if needed
        )
        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())
