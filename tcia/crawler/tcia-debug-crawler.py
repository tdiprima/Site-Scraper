#!/usr/bin/env python3
"""
Debug version of TCIA crawler to identify issues
"""

import logging
import os
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_crawl():
    """Test crawling functionality"""
    base_url = "https://www.cancerimagingarchive.net/"
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    )

    # First, let's check if we can access the site
    logger.info("Testing connection to TCIA...")
    try:
        response = session.get(base_url, timeout=10)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Content length: {len(response.content)}")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return

    # Parse the page
    soup = BeautifulSoup(response.content, "html.parser")
    logger.info(f"Page title: {soup.title.string if soup.title else 'No title'}")

    # Find all links
    all_links = soup.find_all("a", href=True)
    logger.info(f"Total links found: {len(all_links)}")

    # Look for collection links specifically
    collection_links = []
    for link in all_links:
        href = link["href"]
        text = link.get_text(strip=True)

        # Collection URLs typically have /collection/ in them
        if "/collection/" in href:
            absolute_url = urljoin(base_url, href)
            collection_links.append((absolute_url, text))
            logger.debug(f"Collection link: {href} -> {text}")

    logger.info(f"Found {len(collection_links)} collection links on homepage")

    # Now let's try the browse-collections page
    browse_url = "https://www.cancerimagingarchive.net/browse-collections/"
    logger.info(f"\nTrying browse-collections page: {browse_url}")

    try:
        response = session.get(browse_url, timeout=10)
        logger.info(f"Status code: {response.status_code}")

        soup = BeautifulSoup(response.content, "html.parser")

        # Look for table with collections
        tables = soup.find_all("table")
        logger.info(f"Found {len(tables)} tables")

        # Find all links in tables
        table_links = []
        for table in tables:
            for link in table.find_all("a", href=True):
                href = link["href"]
                text = link.get_text(strip=True)
                if "/collection/" in href:
                    absolute_url = urljoin(browse_url, href)
                    table_links.append((absolute_url, text))

        logger.info(f"Found {len(table_links)} collection links in tables")

        # Print first 10 for verification
        logger.info("\nFirst 10 collection URLs found:")
        for url, text in table_links[:10]:
            logger.info(f"  {text}: {url}")

    except Exception as e:
        logger.error(f"Failed to access browse-collections: {e}")

    # Check if the page uses JavaScript to load content
    logger.info("\nChecking for JavaScript indicators...")
    scripts = soup.find_all("script")
    logger.info(f"Number of script tags: {len(scripts)}")

    # Look for common JS frameworks
    for script in scripts:
        src = script.get("src", "")
        if any(
            framework in src.lower()
            for framework in ["react", "angular", "vue", "jquery"]
        ):
            logger.info(f"Found JS framework: {src}")


if __name__ == "__main__":
    test_crawl()
