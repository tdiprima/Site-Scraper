"""
Removes HTML comment lines from the first line of markdown files
"""

import glob
import os


def remove_first_line(file_path):
    try:
        # Read all lines
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        # Check if first line is a markdown comment
        if (
            lines
            and lines[0].strip().startswith("<!--")
            and lines[0].strip().endswith("-->")
        ):
            # Write back all lines except the first
            with open(file_path, "w", encoding="utf-8") as file:
                file.writelines(lines[1:])
            print(f"Processed: {file_path}")
        else:
            print(f"Skipped: {file_path} (first line is not a markdown comment)")
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


# Directory path
directory = "/home/tdiprima/open-webui/data/uploads"

# Find all .md files
md_files = glob.glob(os.path.join(directory, "*.md"))

# Process each file
for md_file in md_files:
    remove_first_line(md_file)
