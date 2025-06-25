# Site Scraper

## Overview
This repository contains a collection of scripts designed for scraping websites, postprocessing the scraped data, and uploading the processed files to Open WebUI. It allows for efficient data collection and management from various web sources.

## Features
- **Web Scraping**: Scripts to crawl entire domains while respecting robots.txt and convert HTML pages into Markdown format.
- **Postprocessing**: Tools to clean and format scraped data by removing unwanted elements such as headers, footers, and navigation bars.
- **File Upload**: Automated scripts to upload processed files to Open WebUI and integrate them into a knowledge base.

## Directory Structure
- **bmi**: Contains scripts specific to the BMI domain.
- **open_webui**: Scraping and processing content from Open WebUI documentation.
- **stonybrook**: Dedicated to scraping and processing content from Stony Brook University.
- **tcia**: Scraping and processing content from The Cancer Imaging Archive.
- **upload**: Scripts to manage the upload of processed content.
- **misc**: Various utility scripts for checks and debugging.
- **tutorial**: Educational materials for web scraping and threading concepts.

## Getting Started
1. **Installation**: Ensure you have Python and dependencies installed. Use requirements.txt if available.
2. **Configuration**: Configure scripts with the necessary tokens and file paths as per your requirements.
3. **Run**: Execute the scripts from the command line as needed. Refer to each script's inline documentation for specific instructions.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
