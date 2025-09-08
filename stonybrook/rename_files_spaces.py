"""
Script to rename files in a directory by replacing spaces with underscores.
"""

import os
from pathlib import Path


def rename_files_with_underscores(directory):
    """
    Rename all files in the specified directory by replacing spaces with underscores.

    Args:
        directory (str): Path to the directory containing files to rename
    """
    # Check if directory exists
    if not Path(directory).exists():
        print(f"Error: Directory '{directory}' does not exist.")
        return

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory.")
        return

    # Counter for renamed files
    renamed_count = 0
    skipped_count = 0

    try:
        # List all files in the directory
        files = os.listdir(directory)

        for filename in files:
            # Full path to the file
            old_path = os.path.join(directory, filename)

            # Skip if it's a directory
            if os.path.isdir(old_path):
                continue

            # Check if filename contains spaces
            if " " in filename:
                # Create new filename with underscores instead of spaces
                new_filename = filename.replace(" ", "_")
                new_path = os.path.join(directory, new_filename)

                # Check if a file with the new name already exists
                if Path(new_path).exists():
                    print(
                        f"Warning: Cannot rename '{filename}' - '{new_filename}' already exists."
                    )
                    skipped_count += 1
                    continue

                try:
                    # Rename the file
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{filename}' -> '{new_filename}'")
                    renamed_count += 1
                except Exception as e:
                    print(f"Error renaming '{filename}': {e}")
                    skipped_count += 1

    except Exception as e:
        print(f"Error reading directory: {e}")
        return

    # Print summary
    print("\nSummary:")
    print(f"  Files renamed: {renamed_count}")
    print(f"  Files skipped: {skipped_count}")
    print(f"  Total files processed: {len(files)}")


def main():
    # Directory to process
    directory = "/home/tdiprima/github/Site-Scraper/stonybrook_content"

    print(f"Processing directory: {directory}")
    print("-" * 50)

    # Call the rename function
    rename_files_with_underscores(directory)


if __name__ == "__main__":
    main()
