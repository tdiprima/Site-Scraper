"""
Vibin' File Cleaner 🔥
This script yeets the messy headers and footers from your .md files, keeping the good stuff.
Just swap "path/to/your/folder" with your actual folder path and you're golden! 💪
Edits files in place, so no extra clutter. Run it and watch the magic happen. 😎
"""
import os
import re

def clean_file_content(content):
    # Define header pattern (from 'Skip Navigation' to common section markers like 'Home', 'About Us', or 'Research Overview')
    header_pattern = r'^Skip Navigation\n(?:.*\n)*?(?=^(?:Who We Are|Research Overview|About Us|\Z))'
    
    # Define footer pattern (from 'See pages' or institute name to the end)
    footer_pattern = r'^(See pages|Institute for Engineering-Driven Medicine|Global Health Institute|Stony Brook University\n.*?\nDiscrimination\n.*?\n©\nAdmin Login\n2025\nStony Brook University)$'
    
    # Remove header
    content = re.sub(header_pattern, '', content, flags=re.MULTILINE)
    
    # Remove footer
    content = re.sub(footer_pattern, '', content, flags=re.MULTILINE)
    
    # Clean up any extra blank lines
    content = re.sub(r'\n\s*\n+', '\n', content).strip()
    
    return content

def process_files_in_folder(folder):
    # Iterate through all files in the folder
    for filename in os.listdir(folder):
        if filename.endswith('.md'):  # Process only markdown files
            file_path = os.path.join(folder, filename)
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Clean the content
            cleaned_content = clean_file_content(content)
            
            # Overwrite the original file with cleaned content
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(cleaned_content)
            
            print(f"Processed and updated {filename}")

if __name__ == "__main__":
    folder = "/home/tdiprima/github/Site-Scraper/stonybrook_content"
    process_files_in_folder(folder)
