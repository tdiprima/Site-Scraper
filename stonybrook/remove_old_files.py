import os
from datetime import datetime

def remove_files_before_timestamp(directory, cutoff_time):
    # Ensure directory exists
    if not os.path.isdir(directory):
        raise ValueError(f"Directory {directory} does not exist")

    # Convert cutoff time to timestamp
    cutoff_timestamp = cutoff_time.timestamp()

    # Iterate through files
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            creation_time = os.stat(file_path).st_ctime  # Creation time on Linux
            if creation_time < cutoff_timestamp:
                try:
                    os.remove(file_path)
                    print(f"Deleted {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")
            else:
                print(f"Keeping {filename}: Created after cutoff")
        else:
            print(f"Skipping {file_path}: Not a file")

# Usage
directory = "stonybrook_content"
cutoff_time = datetime(2025, 6, 2, 16, 55)  # 4:55 PM on June 2, 2025

remove_files_before_timestamp(directory, cutoff_time)
