#!/usr/bin/env python3
"""
Script to move processed files listed in upload_progress.json to a new folder.
"""

import json
import os
import shutil
from pathlib import Path


def move_files_to_uploaded_folder(json_file_path='upload_progress.json', target_folder='uploaded_sbu_files'):
    """
    Read the JSON file and move all processed files to the target folder.
    
    Args:
        json_file_path: Path to the JSON file containing the list of processed files
        target_folder: Name of the folder where files should be moved
    """
    
    # Create the target folder if it doesn't exist
    target_path = Path(target_folder)
    target_path.mkdir(exist_ok=True)
    print(f"Created/verified folder: {target_folder}")
    
    # Read the JSON file
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {json_file_path} not found!")
        return
    except json.JSONDecodeError:
        print(f"Error: {json_file_path} is not valid JSON!")
        return
    
    # Get the list of processed files
    processed_files = data.get('processed_files', [])
    total_files = len(processed_files)
    
    if total_files == 0:
        print("No files to move.")
        return
    
    print(f"Found {total_files} files to move.")
    
    # Move each file
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in processed_files:
        source_path = Path(file_path)
        
        # Check if source file exists
        if not source_path.exists():
            print(f"Warning: File not found - {file_path}")
            skipped_count += 1
            continue
        
        # Preserve the folder structure within the target folder
        # Get the relative path from the first folder (stonybrook_content)
        try:
            # Find the index of 'stonybrook_content' in the path
            parts = source_path.parts
            if 'stonybrook_content' in parts:
                idx = parts.index('stonybrook_content')
                relative_parts = parts[idx+1:]  # Everything after 'stonybrook_content'
            else:
                relative_parts = parts
            
            # Create the full target path preserving folder structure
            target_file_path = target_path.joinpath(*relative_parts)
            
            # Create parent directories if they don't exist
            target_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move the file
            shutil.move(str(source_path), str(target_file_path))
            moved_count += 1
            
            # Print progress every 100 files
            if moved_count % 100 == 0:
                print(f"Progress: {moved_count}/{total_files} files moved...")
                
        except Exception as e:
            print(f"Error moving {file_path}: {str(e)}")
            error_count += 1
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Total files in list: {total_files}")
    print(f"Successfully moved: {moved_count}")
    print(f"Skipped (not found): {skipped_count}")
    print(f"Errors: {error_count}")
    print("="*50)


if __name__ == "__main__":
    # You can customize these paths if needed
    move_files_to_uploaded_folder()
    
    # Alternative usage with custom paths:
    # move_files_to_uploaded_folder('path/to/upload_progress.json', 'custom_folder_name')
