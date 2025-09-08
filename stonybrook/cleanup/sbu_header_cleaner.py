#!/usr/bin/env python3
"""
Removes unwanted header content from RAG documents, particularly
HTML comments with source URLs and SBU search elements
"""

import re
from pathlib import Path


def clean_document(file_path):
    """
    Remove the unwanted header content from a document.

    Args:
        file_path (Path): Path to the file to clean

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        original_content = content

        # Pattern to match the unwanted header content
        # Matches from HTML comment with source URL through the search elements
        pattern = r"<!--\s*Source:\s*https?://[^\s]+\s*-->\s*Search Text\s*Select Search Scope\s*Search This Site\s*Just This Site\s*Search SBU Website\s*SBU Website\s*Search\s*"

        # Remove the unwanted content (case insensitive, multiline)
        cleaned_content = re.sub(
            pattern, "", content, flags=re.IGNORECASE | re.MULTILINE
        )

        # Also handle variations with different whitespace/newlines
        pattern_flexible = r"<!--\s*Source:\s*https?://[^\s]+\s*-->\s*Search\s+Text\s+Select\s+Search\s+Scope\s+Search\s+This\s+Site\s+Just\s+This\s+Site\s+Search\s+SBU\s+Website\s+SBU\s+Website\s+Search\s*"
        cleaned_content = re.sub(
            pattern_flexible, "", cleaned_content, flags=re.IGNORECASE | re.MULTILINE
        )

        # Check if content was actually changed
        if cleaned_content != original_content:
            # Write the cleaned content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
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
    files = [
        f for f in directory.iterdir() if f.is_file() and f.suffix.lower() == ".md"
    ]

    print(f"Found {len(files)} .md files to process...")

    modified_count = 0

    for file_path in files:
        if clean_document(file_path):
            print(f"CLEANED: {file_path}")
            modified_count += 1

    print(f"\nCleaning complete. {modified_count} files were modified.")


if __name__ == "__main__":
    main()
