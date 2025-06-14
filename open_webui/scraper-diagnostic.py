import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def diagnose_site(url):
    """Diagnostic tool to understand the site structure"""
    print(f"Diagnosing: {url}")
    print("=" * 60)
    
    try:
        # Fetch the page
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Compatible; DocsScraper/1.0)'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Check for JavaScript-rendered content
        print("\n1. Checking for JavaScript indicators:")
        scripts = soup.find_all('script')
        print(f"   - Found {len(scripts)} script tags")
        
        # Look for React/Vue/Angular indicators
        react_indicators = ['react', 'React', '__NEXT_DATA__', '_next']
        vue_indicators = ['vue', 'Vue', 'v-if', 'v-for']
        for script in scripts:
            script_text = str(script)
            if any(ind in script_text for ind in react_indicators):
                print("   - ⚠️  Detected React/Next.js - site may be JavaScript-rendered")
            if any(ind in script_text for ind in vue_indicators):
                print("   - ⚠️  Detected Vue.js - site may be JavaScript-rendered")
        
        # 2. Find all links
        print("\n2. Analyzing links:")
        all_links = soup.find_all('a', href=True)
        print(f"   - Total links found: {len(all_links)}")
        
        # Categorize links
        internal_links = []
        external_links = []
        fragment_links = []
        javascript_links = []
        
        domain = urlparse(url).netloc
        
        for link in all_links:
            href = link['href']
            if href.startswith('javascript:'):
                javascript_links.append(href)
            elif href.startswith('#'):
                fragment_links.append(href)
            else:
                absolute_url = urljoin(url, href)
                if urlparse(absolute_url).netloc == domain:
                    internal_links.append(absolute_url)
                else:
                    external_links.append(absolute_url)
        
        print(f"   - Internal links: {len(internal_links)}")
        print(f"   - External links: {len(external_links)}")
        print(f"   - Fragment links (#): {len(fragment_links)}")
        print(f"   - JavaScript links: {len(javascript_links)}")
        
        # 3. Show sample of internal links
        print("\n3. Sample internal links (first 20):")
        for i, link in enumerate(internal_links[:20]):
            print(f"   {i+1}. {link}")
        
        if len(internal_links) > 20:
            print(f"   ... and {len(internal_links) - 20} more")
        
        # 4. Check for navigation patterns
        print("\n4. Navigation structure:")
        nav_elements = soup.find_all(['nav', 'div'], class_=['nav', 'navigation', 'menu', 'sidebar'])
        print(f"   - Found {len(nav_elements)} navigation elements")
        
        # Look for documentation-specific patterns
        doc_patterns = soup.find_all(['a'], href=lambda x: x and any(
            pattern in x for pattern in ['/docs/', '/guide/', '/api/', '/tutorial/']
        ))
        print(f"   - Found {len(doc_patterns)} documentation-style links")
        
        # 5. Check for sitemap
        print("\n5. Checking for sitemap:")
        sitemap_urls = [
            urljoin(url, '/sitemap.xml'),
            urljoin(url, '/sitemap'),
            urljoin(url, '/sitemap.txt')
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                resp = requests.head(sitemap_url, timeout=5)
                if resp.status_code == 200:
                    print(f"   ✓ Found sitemap at: {sitemap_url}")
                    break
            except:
                pass
        else:
            print("   - No sitemap found")
        
        # 6. Check meta tags for generator
        print("\n6. Site generator detection:")
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator:
            print(f"   - Generator: {generator.get('content', 'Unknown')}")
        
        # Check for common static site generators
        if soup.find('div', id='__docusaurus'):
            print("   - Detected: Docusaurus")
        elif soup.find('div', class_='gatsby-focus-wrapper'):
            print("   - Detected: Gatsby")
        elif any('vitepress' in str(s) for s in scripts):
            print("   - Detected: VitePress")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_site("https://docs.openwebui.com/")