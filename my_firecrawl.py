from firecrawl import FirecrawlApp
import os
import sys

# Get API key from environment variable
api_key = os.environ.get('FIRECRAWL_API_KEY')
if not api_key:
    print("Error: FIRECRAWL_API_KEY environment variable is not set.")
    print("Please set it using: export FIRECRAWL_API_KEY='your-api-key'")
    sys.exit(1)


# Initialize the FirecrawlApp with your API key
app = FirecrawlApp(api_key=api_key)

# Crawl a website
crawl_result = app.crawl_url('https://bmi.stonybrookmedicine.edu')

# Access the markdown content
for page in crawl_result:
    print(page['markdown'])
