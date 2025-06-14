import requests
import xml.etree.ElementTree as ET


def debug_sitemap():
    """Debug function to see what's in the sitemap"""
    sitemap_url = "https://docs.openwebui.com/sitemap.xml"

    print(f"Fetching: {sitemap_url}")
    response = requests.get(sitemap_url)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        # Print raw content (first 1000 chars)
        print("\nRaw content (first 1000 chars):")
        print(response.text[:1000])

        # Try to parse
        try:
            root = ET.fromstring(response.content)
            print(f"\nRoot tag: {root.tag}")

            # Print all child tags
            print("\nChild elements:")
            for child in root:
                print(f"  - {child.tag}")
                # Print grandchildren
                for grandchild in child:
                    print(f"    - {grandchild.tag}: {grandchild.text[:50] if grandchild.text else 'None'}")

            # Try different namespace possibilities
            namespaces = [
                {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'},
                {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'},
                {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            ]

            for ns in namespaces:
                print(f"\nTrying namespace: {ns}")
                urls = root.findall('.//url', ns) or root.findall('.//sm:url', ns) or root.findall('.//sitemap:url', ns)
                print(f"Found {len(urls)} URLs")

                if urls:
                    print("First 5 URLs:")
                    for i, url in enumerate(urls[:5]):
                        loc = url.find('loc', ns) or url.find('sm:loc', ns) or url.find('sitemap:loc', ns)
                        if loc is not None and loc.text:
                            print(f"  {i + 1}. {loc.text}")

        except Exception as e:
            print(f"\nError parsing XML: {e}")


if __name__ == "__main__":
    debug_sitemap()
