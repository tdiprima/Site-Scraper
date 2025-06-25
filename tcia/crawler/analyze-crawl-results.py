#!/usr/bin/env python3
"""
Analyze crawl results to find distinct failures and summarize the crawl
"""

import os
import re
from collections import defaultdict, Counter
from datetime import datetime


def parse_log_file(log_content):
    """Parse log content and extract relevant information"""
    
    # Patterns to match different log entries
    patterns = {
        'scraped': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Scraping: (.*?) \(depth: (\d+)\)'),
        'saved': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Saved: (.*)'),
        'found_urls': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - INFO - Found (\d+) new URLs to crawl'),
        'error': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ERROR - (.*)'),
        'skipped_external': re.compile(r'DEBUG - Skipping external URL: (.*)'),
        'skipped_extension': re.compile(r'DEBUG - Skipping file extension: (.*)'),
        'robots_disallow': re.compile(r'DEBUG - Robots\.txt disallows: (.*)'),
        'skipped_special': re.compile(r'DEBUG - Skipping special link: (.*)'),
    }
    
    results = {
        'scraped_pages': [],
        'saved_files': [],
        'errors': [],
        'skipped_external': [],
        'skipped_extensions': [],
        'robots_blocked': [],
        'skipped_special': [],
        'url_counts': []
    }
    
    for line in log_content.split('\n'):
        # Check scraped pages
        match = patterns['scraped'].search(line)
        if match:
            results['scraped_pages'].append({
                'timestamp': match.group(1),
                'url': match.group(2),
                'depth': int(match.group(3))
            })
            
        # Check saved files
        match = patterns['saved'].search(line)
        if match:
            results['saved_files'].append(match.group(2))
            
        # Check found URLs count
        match = patterns['found_urls'].search(line)
        if match:
            results['url_counts'].append(int(match.group(2)))
            
        # Check errors
        match = patterns['error'].search(line)
        if match:
            results['errors'].append({
                'timestamp': match.group(1),
                'message': match.group(2)
            })
            
        # Check skipped URLs
        match = patterns['skipped_external'].search(line)
        if match:
            results['skipped_external'].append(match.group(1))
            
        match = patterns['skipped_extension'].search(line)
        if match:
            results['skipped_extensions'].append(match.group(1))
            
        match = patterns['robots_disallow'].search(line)
        if match:
            results['robots_blocked'].append(match.group(1))
            
        match = patterns['skipped_special'].search(line)
        if match:
            results['skipped_special'].append(match.group(1))
    
    return results


def analyze_failures(results):
    """Analyze and summarize failures"""
    
    print("="*80)
    print("CRAWL ANALYSIS REPORT")
    print("="*80)
    
    # Basic statistics
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   Total pages scraped: {len(results['scraped_pages'])}")
    print(f"   Total files saved: {len(results['saved_files'])}")
    print(f"   Total errors: {len(results['errors'])}")
    
    # Depth analysis
    if results['scraped_pages']:
        depth_counter = Counter(page['depth'] for page in results['scraped_pages'])
        print(f"\n📏 DEPTH DISTRIBUTION:")
        for depth in sorted(depth_counter.keys()):
            print(f"   Depth {depth}: {depth_counter[depth]} pages")
    
    # URL discovery analysis
    if results['url_counts']:
        avg_urls = sum(results['url_counts']) / len(results['url_counts'])
        max_urls = max(results['url_counts'])
        min_urls = min(results['url_counts'])
        print(f"\n🔗 URL DISCOVERY:")
        print(f"   Average URLs per page: {avg_urls:.1f}")
        print(f"   Max URLs found on a page: {max_urls}")
        print(f"   Min URLs found on a page: {min_urls}")
    
    # Error analysis
    if results['errors']:
        print(f"\n❌ ERRORS ({len(results['errors'])} total):")
        
        # Group errors by type
        error_types = defaultdict(list)
        for error in results['errors']:
            msg = error['message']
            # Extract error type
            if 'timeout' in msg.lower():
                error_types['Timeout'].append(msg)
            elif 'connection' in msg.lower():
                error_types['Connection'].append(msg)
            elif '404' in msg or 'not found' in msg.lower():
                error_types['404 Not Found'].append(msg)
            elif '403' in msg or 'forbidden' in msg.lower():
                error_types['403 Forbidden'].append(msg)
            elif '500' in msg or 'server error' in msg.lower():
                error_types['500 Server Error'].append(msg)
            else:
                error_types['Other'].append(msg)
        
        # Show distinct error types with examples
        for error_type, errors in error_types.items():
            print(f"\n   {error_type} ({len(errors)} occurrences):")
            # Show up to 3 unique examples
            unique_errors = list(set(errors))[:3]
            for err in unique_errors:
                # Truncate long error messages
                if len(err) > 150:
                    err = err[:150] + "..."
                print(f"      - {err}")
    
    # Skipped URLs analysis
    print(f"\n🚫 SKIPPED URLS:")
    
    # External domains
    if results['skipped_external']:
        external_domains = Counter()
        for url in results['skipped_external']:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                external_domains[domain] += 1
            except:
                pass
        
        print(f"   External domains skipped ({len(results['skipped_external'])} total):")
        for domain, count in external_domains.most_common(10):
            print(f"      - {domain}: {count} links")
    
    # File extensions
    if results['skipped_extensions']:
        extensions = Counter()
        for url in results['skipped_extensions']:
            # Extract extension
            ext_match = re.search(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
            if ext_match:
                extensions[ext_match.group(1).lower()] += 1
        
        print(f"\n   File extensions skipped ({len(results['skipped_extensions'])} total):")
        for ext, count in extensions.most_common():
            print(f"      - .{ext}: {count} files")
    
    # Robots.txt blocks
    if results['robots_blocked']:
        print(f"\n   Robots.txt blocked URLs: {len(results['robots_blocked'])}")
        # Show a few examples
        for url in list(set(results['robots_blocked']))[:5]:
            print(f"      - {url}")
    
    # Special links (javascript:, mailto:, etc.)
    if results['skipped_special']:
        special_types = Counter()
        for link in results['skipped_special']:
            link_type = link.split(':')[0] if ':' in link else 'other'
            special_types[link_type] += 1
        
        print(f"\n   Special links skipped ({len(results['skipped_special'])} total):")
        for link_type, count in special_types.most_common():
            print(f"      - {link_type}: {count} links")
    
    # Check for missing files (scraped but not saved)
    scraped_urls = {page['url'] for page in results['scraped_pages']}
    if len(scraped_urls) > len(results['saved_files']):
        print(f"\n⚠️  WARNING: {len(scraped_urls) - len(results['saved_files'])} pages were scraped but not saved!")
    
    # Performance metrics
    if results['scraped_pages']:
        # Calculate crawl duration
        timestamps = [datetime.strptime(page['timestamp'], '%Y-%m-%d %H:%M:%S,%f') 
                     for page in results['scraped_pages']]
        duration = (max(timestamps) - min(timestamps)).total_seconds()
        pages_per_second = len(results['scraped_pages']) / duration if duration > 0 else 0
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Crawl duration: {duration:.1f} seconds")
        print(f"   Average speed: {pages_per_second:.2f} pages/second")


def main():
    """Main function to analyze crawl results"""
    
    # Try to read from console output saved to file
    log_file = 'crawl_output.log'
    
    if os.path.exists(log_file):
        print(f"Reading log file: {log_file}")
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
    else:
        print(f"\n⚠️  Log file '{log_file}' not found!")
        print("\nTo capture the crawl output, run the crawler like this:")
        print(f"   python crawler.py 2>&1 | tee {log_file}")
        print("\nOr if you have the output in another file, you can modify this script")
        print("to read from that file instead.")
        return
    
    # Parse and analyze
    results = parse_log_file(log_content)
    analyze_failures(results)
    
    # Also analyze the actual output files
    output_dir = 'tcia_scrape_output'
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        print(f"\n📁 OUTPUT FILES:")
        print(f"   Total markdown files created: {len(files)}")
        
        # Check file sizes
        sizes = []
        for f in files:
            size = os.path.getsize(os.path.join(output_dir, f))
            sizes.append(size)
        
        if sizes:
            avg_size = sum(sizes) / len(sizes)
            print(f"   Average file size: {avg_size/1024:.1f} KB")
            print(f"   Largest file: {max(sizes)/1024:.1f} KB")
            print(f"   Smallest file: {min(sizes)/1024:.1f} KB")
            
            # Find empty files
            empty_files = [files[i] for i, size in enumerate(sizes) if size < 100]
            if empty_files:
                print(f"\n   ⚠️  Very small files (<100 bytes): {len(empty_files)}")
                for f in empty_files[:5]:
                    print(f"      - {f}")


if __name__ == "__main__":
    main()
