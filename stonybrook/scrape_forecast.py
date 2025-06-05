"""
Estimates the number of pages on stonybrook.edu before full scraping

# Basic usage (will take ~2-5 minutes)
python scrape_forecast.py

# Quick mode (headers only, ~30-60 seconds)
python scrape_forecast.py --quick

# Faster sampling with more workers
python scrape_forecast.py --workers 10 --sample 50

# Full analysis with larger sample
python scrape_forecast.py --sample 200 --depth 4

# Analyze a different site
python scrape_forecast.py --url https://cs.stonybrook.edu
"""
import argparse
import concurrent.futures
import time
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class SiteScout:
    def __init__(self, base_url='https://www.stonybrook.edu', 
                 max_sample=100, max_depth=3, max_workers=5, 
                 delay=0.5, quick_mode=False):
        self.base_url = base_url
        self.max_sample = max_sample
        self.max_depth = max_depth
        self.max_workers = max_workers
        self.delay = delay
        self.quick_mode = quick_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Site Size Estimator Bot)'
        })
        
    def extract_links(self, html, base_url):
        """Extract all links from HTML page"""
        links = set()
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Find all elements with href
            for tag in soup.find_all(['a', 'link']):
                href = tag.get('href')
                if href:
                    # Convert to absolute URL
                    absolute_url = urljoin(base_url, href)

                    # Parse and validate
                    parsed = urlparse(absolute_url)

                    # Only keep HTTP/HTTPS links
                    if parsed.scheme in ['http', 'https']:
                        # Remove fragment and normalize
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            clean_url += f"?{parsed.query}"

                        # Skip common non-page resources
                        skip_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', 
                                         '.zip', '.doc', '.docx', '.xls', '.xlsx',
                                         '.ppt', '.pptx', '.mp4', '.mp3'}
                        
                        if not any(clean_url.lower().endswith(ext) for ext in skip_extensions):
                            links.add(clean_url)

        except Exception as e:
            print(f"Error parsing links from {base_url}: {e}")

        return links

    def check_sitemaps(self):
        """Check for sitemaps and count URLs"""
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/sitemap.xml.gz"
        ]
        
        all_sitemap_urls = set()

        for sitemap_url in sitemap_urls:
            try:
                print(f"Checking {sitemap_url}...")
                response = self.session.get(sitemap_url, timeout=10)

                if response.status_code == 200:
                    # Check if it's a sitemap index
                    if 'sitemapindex' in response.text[:1000]:
                        # Parse sitemap index
                        root = ET.fromstring(response.content)
                        sitemap_locs = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')

                        print(f"Found sitemap index with {len(sitemap_locs)} sitemaps")

                        # Fetch each sub-sitemap
                        for loc in sitemap_locs[:10]:  # Limit to first 10 to avoid taking too long
                            try:
                                sub_response = self.session.get(loc.text, timeout=10)
                                if sub_response.status_code == 200:
                                    sub_root = ET.fromstring(sub_response.content)
                                    urls = sub_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                                    all_sitemap_urls.update(url.text for url in urls)
                            except:
                                continue
                    else:
                        # Regular sitemap
                        root = ET.fromstring(response.content)
                        urls = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        all_sitemap_urls.update(url.text for url in urls if url.text)

                    print(f"Total URLs found in sitemaps: {len(all_sitemap_urls)}")
                    return all_sitemap_urls

            except Exception as e:
                print(f"Error checking {sitemap_url}: {e}")
                continue

        return all_sitemap_urls

    def fetch_page_links(self, url):
        """Fetch a single page and extract links"""
        try:
            if self.quick_mode:
                # Just check if page exists
                response = self.session.head(url, timeout=5, allow_redirects=True)
                return url, set(), response.status_code == 200
            else:
                # Full page fetch
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    links = self.extract_links(response.text, url)
                    # Filter for internal links only
                    internal_links = {
                        link for link in links 
                        if 'stonybrook.edu' in urlparse(link).netloc
                    }
                    return url, internal_links, True
                else:
                    return url, set(), False

        except Exception as e:
            return url, set(), False

    def sample_site_concurrent(self):
        """Sample the site using concurrent requests"""
        visited = set()
        to_visit = deque([self.base_url])
        all_discovered_urls = {self.base_url}
        depth_map = {self.base_url: 0}
        level_counts = {0: 1}
        failed_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while len(visited) < self.max_sample and to_visit:
                # Get batch of URLs to process
                batch = []
                batch_size = min(self.max_workers, len(to_visit), self.max_sample - len(visited))

                for _ in range(batch_size):
                    if to_visit:
                        url = to_visit.popleft()
                        if url not in visited and depth_map.get(url, 0) <= self.max_depth:
                            batch.append(url)
                            visited.add(url)

                if not batch:
                    break

                # Process batch concurrently
                future_to_url = {executor.submit(self.fetch_page_links, url): url for url in batch}

                for future in concurrent.futures.as_completed(future_to_url):
                    url, links, success = future.result()

                    if success:
                        all_discovered_urls.update(links)
                        current_depth = depth_map.get(url, 0)

                        # Add new links to queue
                        for link in links:
                            if link not in depth_map:
                                depth_map[link] = current_depth + 1
                                if current_depth + 1 <= self.max_depth:
                                    to_visit.append(link)
                                    level_counts[current_depth + 1] = level_counts.get(current_depth + 1, 0) + 1
                    else:
                        failed_count += 1

                    # Be polite to the server
                    time.sleep(self.delay)

                # Progress update
                print(f"Sampled: {len(visited)}/{self.max_sample}, "
                      f"Discovered: {len(all_discovered_urls)}, "
                      f"Queue: {len(to_visit)}", end='\r')

        print()  # New line after progress updates

        return {
            'visited': visited,
            'discovered': all_discovered_urls,
            'queue_size': len(to_visit),
            'level_counts': level_counts,
            'failed_count': failed_count
        }

    def estimate_total(self):
        """Run the complete estimation process"""
        print(f"🔍 Estimating size of {self.base_url}")
        print(f"Mode: {'Quick (headers only)' if self.quick_mode else 'Full sampling'}")
        print(f"Workers: {self.max_workers}, Sample size: {self.max_sample}\n")

        start_time = datetime.now()
        estimates = {}  # type: dict[str, any]

        # Step 1: Check sitemaps
        print("Step 1: Checking sitemaps...")
        sitemap_urls = self.check_sitemaps()
        if sitemap_urls:
            estimates['sitemap'] = len(sitemap_urls)
        print()

        # Step 2: Sample the site
        if not self.quick_mode or not sitemap_urls:
            print("Step 2: Sampling site structure...")
            sample_results = self.sample_site_concurrent()

            visited_count = len(sample_results['visited'])
            discovered_count = len(sample_results['discovered'])
            queue_size = sample_results['queue_size']
            failed_count = sample_results['failed_count']

            # Combine with sitemap URLs
            all_urls = sample_results['discovered']
            if sitemap_urls:
                all_urls = all_urls.union(sitemap_urls)

            estimates['total_discovered'] = len(all_urls)
            estimates['sample_visited'] = visited_count
            estimates['sample_failed'] = failed_count

            # Calculate growth metrics
            if visited_count > 0:
                avg_links_per_page = discovered_count / visited_count
                discovery_rate = queue_size / visited_count

                # Estimate total pages
                # Conservative: assume we've seen most patterns
                estimates['conservative'] = len(all_urls) * 1.5

                # Moderate: factor in queue growth
                estimates['moderate'] = len(all_urls) * (1 + discovery_rate * 0.5)

                # Aggressive: exponential growth potential
                estimates['aggressive'] = len(all_urls) * (1 + discovery_rate) ** 2

                # Best guess: weighted average
                if sitemap_urls:
                    # If we have sitemap, weight it heavily
                    estimates['best_guess'] = int(
                        0.6 * estimates.get('sitemap', 0) +
                        0.3 * estimates.get('moderate', 0) +
                        0.1 * estimates.get('aggressive', 0)
                    )
                else:
                    # No sitemap, rely on sampling
                    estimates['best_guess'] = int(
                        0.4 * estimates.get('conservative', 0) +
                        0.4 * estimates.get('moderate', 0) +
                        0.2 * estimates.get('aggressive', 0)
                    )
                
                estimates['metrics'] = {
                    'avg_links_per_page': round(avg_links_per_page, 2),
                    'discovery_rate': round(discovery_rate, 2),
                    'level_counts': sample_results['level_counts']
                }
        
        # Calculate runtime
        runtime = (datetime.now() - start_time).total_seconds()

        # Display results
        print("\n" + "=" * 50)
        print("📊 ESTIMATION RESULTS")
        print("=" * 50)

        if 'sitemap' in estimates:
            print(f"Sitemap URLs found: {estimates['sitemap']:,}")

        if 'total_discovered' in estimates:
            print(f"Unique URLs discovered: {estimates['total_discovered']:,}")
            print(f"Pages sampled: {estimates['sample_visited']:,}")
            print(f"Failed requests: {estimates['sample_failed']}")

        if 'best_guess' in estimates:
            print(f"\n📈 Size Estimates:")
            print(f"  Conservative: {int(estimates['conservative']):,} pages")
            print(f"  Moderate: {int(estimates['moderate']):,} pages")
            print(f"  Aggressive: {int(estimates['aggressive']):,} pages")
            print(f"\n🎯 Best Guess: {estimates['best_guess']:,} pages")

            if 'metrics' in estimates:
                print(f"\n📊 Metrics:")
                print(f"  Avg links/page: {estimates['metrics']['avg_links_per_page']}")
                print(f"  Discovery rate: {estimates['metrics']['discovery_rate']}")
                print(f"  Depth distribution: {estimates['metrics']['level_counts']}")

        print(f"\n⏱️  Runtime: {runtime:.1f} seconds")
        print("=" * 50)

        return estimates


def main():
    parser = argparse.ArgumentParser(description='Estimate the size of a website before scraping')
    parser.add_argument('--url', default='https://www.stonybrook.edu', help='Base URL to analyze')
    parser.add_argument('--sample', type=int, default=100, help='Number of pages to sample (default: 100)')
    parser.add_argument('--depth', type=int, default=3, help='Maximum crawl depth (default: 3)')
    parser.add_argument('--workers', type=int, default=5, help='Number of concurrent workers (default: 5)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--quick', action='store_true', help='Quick mode - only check headers, not full content')

    args = parser.parse_args()

    scout = SiteScout(
        base_url=args.url,
        max_sample=args.sample,
        max_depth=args.depth,
        max_workers=args.workers,
        delay=args.delay,
        quick_mode=args.quick
    )

    scout.estimate_total()


if __name__ == '__main__':
    main()
