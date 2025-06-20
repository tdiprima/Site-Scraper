import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import requests

# ========== CONFIG ==========
token = "JWT_TOKEN"
knowledge_id = "bbbc10f3-b733-4252-b9ea-a5cf85f30870" 
directory_path = '/home/tdiprima/stonybrook_content'
uploaded_file_ids_path = 'uploaded.txt'
added_to_collection_path = 'added_to_collection.txt'
throttle_seconds = 0.1  # Reduced throttle for parallel processing
max_workers = 16  # Use 16 workers (half your cores for I/O bound tasks)

# Thread-safe locks for file operations
upload_lock = threading.Lock()
collection_lock = threading.Lock()

# ============================

def upload_file(token, file_path):
    url = 'http://localhost:3000/api/v1/files/'
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, headers=headers, files=files, timeout=30)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        raise


def add_file_to_knowledge(token, knowledge_id, file_id):
    url = f'http://localhost:3000/api/v1/knowledge/{knowledge_id}/file/add'
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {'file_id': file_id}
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error adding file {file_id} to collection: {e}")
        raise


def load_progress(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_progress_threadsafe(file_path, item, lock):
    with lock:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(str(item) + '\n')


def process_file(file_info, uploaded_files, added_file_ids):
    """Process a single file: upload and add to collection"""
    filename, file_path = file_info
    
    # Check if already uploaded (thread-safe check)
    with upload_lock:
        if filename in uploaded_files:
            print(f"Already uploaded {filename}, skipping.")
            return f"Skipped: {filename} (already uploaded)"
    
    print(f"[Thread {threading.current_thread().name}] Uploading {filename}...")
    
    try:
        # Upload the file
        result = upload_file(token, file_path)
        file_id = result.get('id')
        
        if not file_id:
            return f"Error: No file ID returned for {filename}"
        
        # Mark as uploaded
        save_progress_threadsafe(uploaded_file_ids_path, filename, upload_lock)
        uploaded_files.add(filename)  # Update in-memory set
        
        print(f"[Thread {threading.current_thread().name}] Uploaded {filename}, ID: {file_id}")
        
        # Check if already added to collection
        with collection_lock:
            if file_id in added_file_ids:
                return f"Skipped: {filename} (already in collection)"
        
        # Add to knowledge collection
        response = add_file_to_knowledge(token, knowledge_id, file_id)
        
        # Mark as added to collection
        save_progress_threadsafe(added_to_collection_path, file_id, collection_lock)
        added_file_ids.add(file_id)  # Update in-memory set
        
        print(f"[Thread {threading.current_thread().name}] Added {filename} to collection")
        
        # Respectful pause
        time.sleep(throttle_seconds)
        
        return f"Success: {filename} -> {file_id}"
        
    except Exception as e:
        return f"Error processing {filename}: {str(e)}"


def main():
    # Validate directory
    if not os.path.isdir(directory_path):
        raise ValueError(f"The directory {directory_path} does not exist")
    
    # Load existing progress
    uploaded_files = load_progress(uploaded_file_ids_path)
    added_file_ids = load_progress(added_to_collection_path)
    
    print(f"Loaded progress: {len(uploaded_files)} uploaded files, {len(added_file_ids)} files in collection")
    
    # Get list of files to process
    files_to_process = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            files_to_process.append((filename, file_path))
    
    print(f"Found {len(files_to_process)} files to process")
    
    if not files_to_process:
        print("No files to process!")
        return
    
    # Process files with thread pool
    results = []
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="FileUploader") as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(process_file, file_info, uploaded_files, added_file_ids): file_info[0] 
            for file_info in files_to_process
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                print(f"Completed: {result}")
            except Exception as e:
                error_msg = f"Exception for {filename}: {str(e)}"
                results.append(error_msg)
                print(error_msg)
    
    # Summary
    print("\n" + "="*50)
    print("PROCESSING COMPLETE")
    print("="*50)
    
    successes = [r for r in results if r.startswith("Success:")]
    skipped = [r for r in results if r.startswith("Skipped:")]
    errors = [r for r in results if r.startswith("Error:") or r.startswith("Exception:")]
    
    print(f"✅ Successful: {len(successes)}")
    print(f"⏭️  Skipped: {len(skipped)}")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    print("\n✅ Done! Safe to re-run if anything went wrong.")


if __name__ == "__main__":
    main()