"""
Get size of output directory in MB
Change directory path as needed
"""
import os

def get_directory_size(directory):
    total_size = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            total_size += os.path.getsize(file_path)
        elif os.path.isdir(file_path):
            total_size += get_directory_size(file_path)  # Recursively include subdirectories
    return total_size

# Directory path
directory = "/home/tdiprima/github/Site-Scraper/stonybrook_content"

# Calculate size in bytes and convert to MB
try:
    total_bytes = get_directory_size(directory)
    total_mb = total_bytes / (1024 * 1024)  # Convert bytes to MB
    print(f"Total size of {directory}: {total_mb:.2f} MB")
except Exception as e:
    print(f"Error: {e}")
