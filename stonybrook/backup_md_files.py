import os
import shutil
from pathlib import Path


def backup_md_files(source_dir, backup_dir):
    # Ensure backup directory exists
    Path(backup_dir).mkdir(parents=True, exist_ok=True)

    # Count total files for progress
    md_files = [f for f in os.listdir(source_dir) if f.endswith('.md')]
    total = len(md_files)

    for i, filename in enumerate(md_files, 1):
        source_path = os.path.join(source_dir, filename)
        backup_path = os.path.join(backup_dir, filename)
        shutil.copy2(source_path, backup_path)
        print(f"Copied {filename} ({i}/{total})")


if __name__ == "__main__":
    source = "/home/tdiprima/github/Site-Scraper/stonybrook_content"
    backup = "/home/tdiprima/backup"
    if os.path.isdir(source):
        backup_md_files(source, backup)
        print("Backup complete!")
    else:
        print("Invalid source directory")
