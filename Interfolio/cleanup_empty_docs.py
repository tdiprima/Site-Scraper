#!/usr/bin/env python3
"""
Clean up empty Interfolio documentation files
Removes markdown files that contain the "no relevant articles" message

Basic usage (with backup):
python cleanup_empty_docs.py

Dry run (see what would be removed):
python cleanup_empty_docs.py --dry-run

Delete without backup:
python cleanup_empty_docs.py --no-backup

Specify different folder:
python cleanup_empty_docs.py /path/to/docs/folder

Verbose output:
python cleanup_empty_docs.py -v
"""

import os
import logging
from pathlib import Path
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_file_for_empty_content(filepath):
    """
    Check if a file contains the empty content message
    
    Args:
        filepath: Path to the markdown file
        
    Returns:
        bool: True if file contains the empty message, False otherwise
    """
    empty_messages = [
        "Sorry, we didn't find any relevant articles for you.",
        "Retry later"
    ]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            return any(message in content for message in empty_messages)
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return False


def clean_empty_docs(docs_folder, backup=True):
    """
    Remove documentation files that contain the empty content message
    
    Args:
        docs_folder: Path to the folder containing markdown files
        backup: If True, move files to backup folder instead of deleting
    """
    docs_path = Path(docs_folder)
    
    if not docs_path.exists():
        logger.error(f"Documentation folder not found: {docs_folder}")
        return
    
    # Create backup folder if needed
    backup_folder = None
    if backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = docs_path.parent / f"removed_docs_{timestamp}"
        backup_folder.mkdir(exist_ok=True)
        logger.info(f"Backup folder created: {backup_folder}")
    
    # Statistics
    total_files = 0
    removed_files = 0
    checked_files = 0
    
    # Process all markdown files
    for filepath in docs_path.glob("*.md"):
        total_files += 1
        filename = filepath.name
        
        logger.debug(f"Checking: {filename}")
        
        if check_file_for_empty_content(filepath):
            checked_files += 1
            
            if backup and backup_folder:
                # Move to backup folder
                backup_path = backup_folder / filename
                try:
                    shutil.move(str(filepath), str(backup_path))
                    logger.info(f"Moved to backup: {filename}")
                    removed_files += 1
                except Exception as e:
                    logger.error(f"Failed to move {filename}: {e}")
            else:
                # Delete the file
                try:
                    filepath.unlink()
                    logger.info(f"Deleted: {filename}")
                    removed_files += 1
                except Exception as e:
                    logger.error(f"Failed to delete {filename}: {e}")
    
    # Summary report
    logger.info("\n" + "="*50)
    logger.info("CLEANUP SUMMARY")
    logger.info("="*50)
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Files with empty content: {checked_files}")
    logger.info(f"Files removed: {removed_files}")
    logger.info(f"Files remaining: {total_files - removed_files}")
    
    if backup and backup_folder and removed_files > 0:
        logger.info(f"\nRemoved files backed up to: {backup_folder}")


def list_empty_files(docs_folder):
    """
    List all files that would be removed (dry run)
    
    Args:
        docs_folder: Path to the folder containing markdown files
    """
    docs_path = Path(docs_folder)
    
    if not docs_path.exists():
        logger.error(f"Documentation folder not found: {docs_folder}")
        return
    
    empty_files = []
    
    for filepath in docs_path.glob("*.md"):
        if check_file_for_empty_content(filepath):
            empty_files.append(filepath.name)
    
    if empty_files:
        logger.info(f"\nFound {len(empty_files)} files with empty content:")
        for filename in sorted(empty_files):
            logger.info(f"  - {filename}")
    else:
        logger.info("\nNo files found with empty content.")
    
    return empty_files


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up empty Interfolio documentation files"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default="interfolio_docs",
        help="Path to documentation folder (default: interfolio_docs)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be removed without actually removing them"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Delete files instead of moving to backup folder"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Execute appropriate action
    if args.dry_run:
        logger.info(f"DRY RUN - Checking folder: {args.folder}")
        list_empty_files(args.folder)
    else:
        logger.info(f"Processing folder: {args.folder}")
        clean_empty_docs(args.folder, backup=not args.no_backup)


if __name__ == "__main__":
    main()
