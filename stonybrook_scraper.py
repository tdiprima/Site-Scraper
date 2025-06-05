"""
stonybrook_scraper.py

Crawl all pages under https://www.stonybrook.edu/*, convert each to markdown,
excluding headers, footers, and navs, and save as separate .md files in stonybrook_content.
Respects robots.txt and skips PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, PNG, JPG, JPEG files.

Dependencies: requests, beautifulsoup4, markdownify
"""
import os
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse
import threading
from queue import Queue, Empty
import signal

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Config
START_URL = "https://www.stonybrook.edu/"
ALLOWED_DOMAIN = "www.stonybrook.edu"
ALLOWED_URL_PREFIX = "https://www.stonybrook.edu/"
OUTPUT_DIR = "stonybrook_content"
VISITED_FILE = "visited.txt"
QUEUE_FILE = "queue.txt"
SITEMAP_URL = "https://www.stonybrook.edu/sitemap.xml"
REQUEST_TIMEOUT = 10  # seconds
SLEEP_TIME = 1.5

# Multi-threading config
NUM_THREADS = 20  # Number of concurrent threads
MAX_PAGES = 20000  # Reasonable limit for a university website

# File extensions to skip
SKIP_EXTENSIONS = [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg"]
SKIP_PATTERNS = ["calendar", "event", "search", "print", "/pdf/", "export", "feed", "rss"]

# Setup
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global variables for thread coordination
visited = set()
visited_lock = threading.Lock()
queue_lock = threading.Lock()
file_lock = threading.Lock()
url_queue = Queue()
stop_crawl = threading.Event()
pages_crawled = 0
pages_crawled_lock = threading.Lock()

# Setup robots.txt parser
ROBOTS_URL = f"{ALLOWED_URL_PREFIX}robots.txt"
USER_AGENT = "*"
rp = urllib.robotparser.RobotFileParser()
rp.set_url(ROBOTS_URL)
try:
    rp.read()
    test_allowed = rp.can_fetch(USER_AGENT, START_URL)
    if not test_allowed:
        print("⚠️  robots.txt not available or not allowing crawling. Ignoring robots.txt and proceeding.")
        rp = None
    else:
        print("✅ robots.txt loaded.")
except Exception as e:
    print(f"⚠️  Could not read robots.txt: {e}")
    rp = None  # Fail open: allow everything

# Load or initialize visited set
if os.path.exists(VISITED_FILE):
    with open(VISITED_FILE, "r", encoding="utf-8") as f:
        visited = set(line.strip() for line in f if line.strip())
else:
    visited = set()


def get_urls_from_sitemap(sitemap_url):
    """
    # Commented out as requested
    try:
        resp = requests.get(sitemap_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        urls = [loc.text.strip() for loc in soup.find_all("loc")]
        print(f"✅ Found {len(urls)} URLs in sitemap.")
        return urls
    except Exception as e:
        print(f"⚠️  Could not load sitemap: {e}")
        return []
    """
    return []


def looks_like_trap(url):
    parsed = urlparse(url)
    if parsed.query and not parsed.path.endswith(('.html', '.htm')):
        return True
    for pattern in SKIP_PATTERNS:
        if pattern in url.lower():
            return True
    return False


def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove headers, footers, navs by tag name
    for tag in soup.find_all(['header', 'footer', 'nav', 'aside']):
        tag.decompose()
    
    # Remove common header/footer patterns by class or id
    header_footer_patterns = [
        # Common class patterns
        {'class': lambda x: x and any(pattern in ' '.join(x).lower() for pattern in 
            ['header', 'footer', 'navigation', 'navbar', 'topbar', 'top-bar', 
             'breadcrumb', 'menu', 'sidebar', 'social', 'copyright', 'meta',
             'toolbar', 'masthead', 'banner', 'top-navigation', 'main-nav',
             'site-header', 'site-footer', 'page-header', 'page-footer'])},
        # Common ID patterns
        {'id': lambda x: x and any(pattern in x.lower() for pattern in 
            ['header', 'footer', 'nav', 'navigation', 'menu', 'breadcrumb',
             'topbar', 'top-bar', 'sidebar', 'banner', 'masthead'])}
    ]
    
    for pattern in header_footer_patterns:
        for element in soup.find_all(attrs=pattern):
            element.decompose()
    
    # Remove elements that commonly contain navigation
    for tag in soup.find_all(['ul', 'ol', 'div']):
        # Check if it's likely a menu (lots of links, little text)
        links = tag.find_all('a')
        if len(links) > 5:
            text_content = tag.get_text(strip=True)
            link_text = ''.join([a.get_text(strip=True) for a in links])
            # If most of the content is link text, it's probably navigation
            if len(link_text) > 0 and len(link_text) / max(len(text_content), 1) > 0.7:
                tag.decompose()
    
    # Find main content
    selectors = [
        ('main', {}),
        ('div', {'role': 'main'}),
        ('div', {'class': 'region-content'}),
        ('article', {}),
        ('div', {'id': 'content'}),
        ('div', {'class': lambda x: x and 'content' in ' '.join(x).lower()}),
        ('div', {'class': lambda x: x and 'main' in ' '.join(x).lower()})
    ]
    main_content = None
    for tag, attrs in selectors:
        found = soup.find(tag, attrs=attrs)
        if found:
            main_content = found
            break
    
    if not main_content:
        # Try to find the largest content block
        content_divs = soup.find_all('div')
        if content_divs:
            # Find div with most text content
            main_content = max(content_divs, 
                             key=lambda d: len(d.get_text(strip=True)) 
                             if d.get_text(strip=True) else 0)
    
    if not main_content:
        main_content = soup.find("body")
    
    if not main_content:
        return ""
    
    # Remove scripts and styles
    for el in main_content.find_all(['script', 'style', 'noscript']):
        el.decompose()
    
    # Remove common header elements that might be inside main content
    for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True).lower()
        # Remove headers that are likely site-wide headers
        if any(pattern in text for pattern in 
               ['stony brook', 'university', 'navigation', 'menu', 'search',
                'login', 'sign in', 'contact us', 'quick links']):
            # But keep it if it's the main page title
            if tag.name != 'h1' or len(main_content.find_all('h1')) > 1:
                tag.decompose()
    
    # Remove all hyperlinks but keep their text
    # This is more thorough - it extracts text and removes the entire <a> tag
    for a in main_content.find_all('a'):
        # Get the text content
        text = a.get_text()
        # Replace the entire <a> tag with just its text
        a.replace_with(text)
    
    # Also remove any href attributes that might remain on other elements
    for tag in main_content.find_all(True):
        if 'href' in tag.attrs:
            del tag.attrs['href']
    
    # Convert to markdown with ATX-style headers
    markdown = md(str(main_content), heading_style="ATX", strip=['a'])
    
    # Additional cleanup to ensure no markdown links remain
    # Remove any [text](url) patterns that might have been created
    import re
    markdown = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', markdown)
    
    # Post-process to remove common header/footer text patterns
    lines = markdown.split('\n')
    filtered_lines = []
    skip_patterns = [
        'skip to main content', 'skip to content', 'skip navigation',
        'breadcrumb', 'you are here', 'home >', 'back to top',
        'share this page', 'print this page', 'last modified',
        'copyright', '©', 'all rights reserved', 'privacy policy',
        'terms of use', 'accessibility', 'contact us'
    ]
    
    for line in lines:
        line_lower = line.strip().lower()
        # Skip lines that are likely header/footer content
        if not any(pattern in line_lower for pattern in skip_patterns):
            filtered_lines.append(line)
    
    markdown = '\n'.join(filtered_lines)
    
    return markdown.strip()


def worker_thread(thread_id):
    """Worker thread function that processes URLs from the queue"""
    global pages_crawled
    
    while not stop_crawl.is_set():
        try:
            # Get URL from queue with timeout
            url = url_queue.get(timeout=5)
        except Empty:
            # No more URLs in queue, check if we should continue
            if url_queue.empty():
                time.sleep(2)  # Wait a bit for new URLs
                if url_queue.empty():  # Still empty, we're done
                    break
            continue
        
        url_no_fragment = urlparse(url)._replace(fragment="").geturl()
        
        # Check if already visited
        with visited_lock:
            if url_no_fragment in visited:
                url_queue.task_done()
                continue
            visited.add(url_no_fragment)
        
        # Check page limit
        with pages_crawled_lock:
            if pages_crawled >= MAX_PAGES:
                print(f"🛑 Reached maximum page limit ({MAX_PAGES}). Stopping crawl.")
                stop_crawl.set()
                url_queue.task_done()
                break
            pages_crawled += 1
            current_count = pages_crawled
        
        # robots.txt check before crawling
        if rp is not None and not rp.can_fetch(USER_AGENT, url_no_fragment):
            print(f"[Thread {thread_id}] 🚫 Blocked by robots.txt: {url_no_fragment}")
            url_queue.task_done()
            continue
        
        print(f"[Thread {thread_id}] 🔍 Crawling ({current_count}/{MAX_PAGES}): {url_no_fragment}")
        
        # Save to visited log
        with file_lock:
            with open(VISITED_FILE, "a", encoding="utf-8") as f:
                f.write(url_no_fragment + "\n")
        
        try:
            resp = requests.get(url_no_fragment, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Thread {thread_id}] ⚠️  Skipping {url_no_fragment!r}: {e}")
            url_queue.task_done()
            continue
        
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        
        # Enqueue internal links, skip docs, keep to allowed domain and prefix
        new_urls = []
        for a in soup.find_all("a", href=True):
            href = urljoin(url_no_fragment, a["href"])
            parsed = urlparse(href)
            
            # Remove fragment (anchor)
            href_no_fragment = parsed._replace(fragment="").geturl()
            path = parsed.path.lower()
            
            # Skip unwanted extensions anywhere in path
            if any(ext in path for ext in SKIP_EXTENSIONS):
                continue
            if looks_like_trap(href_no_fragment):
                continue
            
            if (parsed.netloc == ALLOWED_DOMAIN and 
                href_no_fragment.startswith(ALLOWED_URL_PREFIX)):
                
                # Check if URL is new
                with visited_lock:
                    if href_no_fragment not in visited:
                        if rp is None or rp.can_fetch(USER_AGENT, href_no_fragment):
                            new_urls.append(href_no_fragment)
        
        # Add new URLs to queue
        for new_url in new_urls:
            url_queue.put(new_url)
        
        try:
            # Clean and extract main content
            markdown = clean_html(html)
            if not markdown or len(markdown) < 50:
                print(f"[Thread {thread_id}] ⚠️  Not enough main content found at {url}, skipping.")
                url_queue.task_done()
                continue
            
            # Save file
            parsed_start = urlparse(url)
            path = parsed_start.path.strip("/").replace("/", "_") or "index"
            filename = f"{parsed_start.netloc.replace('.', '_')}_{path}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            with file_lock:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown)
            
            print(f"[Thread {thread_id}] ✅  Saved {url} → {filepath}")
        except Exception as e:
            print(f"[Thread {thread_id}] 💥 Error processing {url}: {e}")
        
        url_queue.task_done()
        time.sleep(SLEEP_TIME / NUM_THREADS)  # Distribute sleep across threads


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Crawl interrupted by user. Shutting down threads...\n")
    stop_crawl.set()


# Load or initialize queue
initial_urls = [START_URL]
if os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        file_urls = [line.strip() for line in f if line.strip()]
        initial_urls.extend(file_urls)

# Commented out sitemap loading as requested
# sitemap_urls = get_urls_from_sitemap(SITEMAP_URL)
# initial_urls.extend(sitemap_urls)

# Remove any skipped extensions and traps
initial_urls = [url for url in initial_urls if not any(ext in url.lower() for ext in SKIP_EXTENSIONS)]
initial_urls = [url for url in initial_urls if not looks_like_trap(url)]

# Add initial URLs to queue
for url in initial_urls:
    url_queue.put(url)

print(f"🚀 Starting crawl with {NUM_THREADS} threads...")
print(f"📊 Maximum pages to crawl: {MAX_PAGES}")
print(f"📁 Initial queue size: {url_queue.qsize()}")
print("(Press Ctrl+C to stop anytime)\n")

# Set up signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)

# Create and start worker threads
threads = []
for i in range(NUM_THREADS):
    t = threading.Thread(target=worker_thread, args=(i+1,))
    t.daemon = True
    t.start()
    threads.append(t)

try:
    # Wait for all threads to complete or stop signal
    for t in threads:
        t.join()
    
    # Wait for queue to be empty
    url_queue.join()
    
except KeyboardInterrupt:
    print("\n🛑 Crawl interrupted by user. Shutting down...\n")
    stop_crawl.set()

finally:
    # Save remaining queue items
    remaining_urls = []
    while not url_queue.empty():
        try:
            remaining_urls.append(url_queue.get_nowait())
        except Empty:
            break
    
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        for item in remaining_urls:
            f.write(item + "\n")
    
    print(f"\n📊 Total pages crawled: {pages_crawled}")
    print(f"📁 Queue saved to {QUEUE_FILE} ({len(remaining_urls)} URLs remaining)")
    print(f"📁 Visited URLs saved to {VISITED_FILE}")
    print("👋 Bye!")
