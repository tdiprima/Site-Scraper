#!/usr/bin/env python3
"""
Script to remove Stony Brook Experts header content from RAG documents.
Removes the entire experts search interface block.
"""

import re
from pathlib import Path


def clean_document(file_path):
    """
    Remove the Stony Brook Experts header content from a document.

    Args:
        file_path (Path): Path to the file to clean

    Returns:
        bool: True if file was modified, False otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        original_content = content

        # Pattern to match the Stony Brook Experts header block
        # This matches the entire block from "Stony Brook Experts" through "Close"
        pattern = r"Stony\s+Brook\s+Experts\s+an\s+online\s+search\s+tool\s+for\s+members\s+of\s+the\s+media\s+to\s+identify\s+experts\s+at\s+Stony\s+Brook\s+Search\s+experts:\s+Search\s+or\s+Browse\s+experts:\s+View\s+all\s+departments\s+View\s+all\s+topics\s+View\s+all\s+experts\s+Close\s*"

        # Remove the unwanted content (case insensitive, multiline)
        cleaned_content = re.sub(
            pattern, "", content, flags=re.IGNORECASE | re.MULTILINE
        )

        # Also try a more flexible pattern that handles various whitespace/newlines
        pattern_flexible = r"Stony\s+Brook\s+Experts\s*an\s+online\s+search\s+tool\s+for\s+members\s+of\s+the\s+media\s+to\s+identify\s+experts\s+at\s+Stony\s+Brook\s*Search\s+experts:\s*Search\s*or\s*Browse\s+experts:\s*View\s+all\s+departments\s+View\s+all\s+topics\s+View\s+all\s+experts\s+Close\s*"
        cleaned_content = re.sub(
            pattern_flexible, "", cleaned_content, flags=re.IGNORECASE | re.MULTILINE
        )

        # Even more flexible pattern with .* for any whitespace/newlines between sections
        pattern_very_flexible = r"Stony\s+Brook\s+Experts.*?an\s+online\s+search\s+tool.*?Search\s+experts:.*?Search.*?or.*?Browse\s+experts:.*?View\s+all\s+departments.*?View\s+all\s+topics.*?View\s+all\s+experts.*?Close"
        cleaned_content = re.sub(
            pattern_very_flexible,
            "",
            cleaned_content,
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
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
