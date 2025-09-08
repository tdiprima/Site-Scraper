#!/usr/bin/env python3
"""
Script to remove documents that contain 404 error messages.
Deletes files that contain the exact text "Oops! That's a 404..."
"""

import os
from pathlib import Path


def check_and_remove_404(file_path):
    """
    Check if a document contains 404 error text and remove it if so.

    Args:
        file_path (Path): Path to the file to check

    Returns:
        bool: True if file was removed, False otherwise
    """
    try:
        content = file_path.read_text(encoding="utf-8")

        # Check if the file contains the 404 error message
        if "Oops! That's a 404..." in content:
            file_path.unlink()
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

    removed_count = 0

    for file_path in files:
        if check_and_remove_404(file_path):
            print(f"REMOVED: {file_path}")
            removed_count += 1

    print(f"\nProcessing complete. {removed_count} files were removed.")


if __name__ == "__main__":
    main()
