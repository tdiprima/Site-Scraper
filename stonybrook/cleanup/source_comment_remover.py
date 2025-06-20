#!/usr/bin/env python3
"""
Script to remove source HTML comments from the top of RAG documents.
Removes comments like: <!-- Source: https://www.stonybrook.edu/some-page/ -->
"""

import re
from pathlib import Path

def clean_document(file_path):
    """
    Remove the source comment from the top of a document.
    
    Args:
        file_path (Path): Path to the file to clean
        
    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match source comments at the beginning of the file
        # Matches <!-- Source: [URL] --> with optional whitespace before/after
        pattern = r'^\s*<!--\s*Source:\s*https?://[^\s]+\s*-->\s*'
        
        # Remove the source comment (case insensitive, multiline)
        cleaned_content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Check if content was actually changed
        if cleaned_content != original_content:
            # Write the cleaned content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    directory_path = "/home/tdiprima/stonybrook_content"
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return
    
    # Get all .md files in the directory (non-recursive)
    files = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == '.md']
    
    print(f"Found {len(files)} .md files to process...")
    
    modified_count = 0
    
    for file_path in files:
        if clean_document(file_path):
            print(f"CLEANED: {file_path}")
            modified_count += 1
    
    print(f"\nCleaning complete. {modified_count} files were modified.")

if __name__ == '__main__':
    main()
