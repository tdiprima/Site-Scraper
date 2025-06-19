"""
AnythingLLM Bulk Document Uploader - Fixed Version
This script handles bulk uploading without automatic embedding
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'anythingllm_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)


class AnythingLLMUploader:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        self.uploaded_documents = []  # Track uploaded document info
        
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/auth",
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions"""
        return [
            '.txt', '.pdf', '.doc', '.docx', '.csv', '.json', 
            '.md', '.html', '.xml', '.rtf', '.odt', '.xls', 
            '.xlsx', '.ppt', '.pptx'
        ]

    def upload_document_to_folder(self, file_path: str, folder_name: str = None) -> Dict:
        """
        Upload a single document to AnythingLLM with optional folder specification
        """
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                
                # Add folder parameter if specified
                data = {}
                if folder_name:
                    data['folder'] = folder_name
                
                logging.info(f"Uploading: {file_path}")

                response = requests.post(
                    f"{self.base_url}/api/v1/document/upload",
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    logging.info(f"Upload successful: {file_path}")
                    
                    # Track uploaded document info
                    if "documents" in result and result["documents"]:
                        doc_info = {
                            'file_path': file_path,
                            'document_id': result["documents"][0].get("id"),
                            'title': result["documents"][0].get("title"),
                            'folder': folder_name or 'Custom Documents'
                        }
                        self.uploaded_documents.append(doc_info)
                    
                    return result
                else:
                    logging.error(f"Upload failed for {file_path}: Status {response.status_code}")
                    return {"error": f"Status {response.status_code}: {response.text}"}

        except Exception as e:
            logging.error(f"Error uploading {file_path}: {str(e)}")
            return {"error": str(e)}

    def get_all_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """Get all supported files from directory"""
        supported_extensions = self.get_supported_extensions()
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if any(filename.lower().endswith(ext) for ext in supported_extensions):
                        if os.path.getsize(file_path) > 0:
                            files.append(file_path)
        else:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in supported_extensions):
                    if os.path.getsize(file_path) > 0:
                        files.append(file_path)
        
        return sorted(files)  # Sort for consistent ordering

    def bulk_upload_with_folders(self, directory_path: str, workspace_slug: str,
                                max_workers: int = 5, batch_size: int = 100,
                                delay_between_batches: float = 1.0,
                                use_batch_folders: bool = True) -> Dict:
        """
        Bulk upload documents with optional batch folders
        """
        # Get all files
        files = self.get_all_files(directory_path)
        total_files = len(files)

        logging.info(f"Found {total_files} supported files to upload")

        if total_files == 0:
            return {"error": "No supported files found"}

        # Initialize counters
        successful_uploads = 0
        failed_uploads = 0
        batch_results = []

        # Process files in batches
        for batch_num, batch_start in enumerate(range(0, total_files, batch_size), 1):
            batch_end = min(batch_start + batch_size, total_files)
            batch_files = files[batch_start:batch_end]
            
            # Create folder name for this batch if requested
            folder_name = None
            if use_batch_folders:
                folder_name = f"Batch_{batch_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logging.info(f"Processing batch {batch_num}: files {batch_start + 1} to {batch_end}")
            if folder_name:
                logging.info(f"  Using folder: {folder_name}")

            batch_successful = 0
            batch_failed = 0

            # Upload files in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                upload_futures = {
                    executor.submit(self.upload_document_to_folder, file_path, folder_name): file_path
                    for file_path in batch_files
                }

                for future in as_completed(upload_futures):
                    file_path = upload_futures[future]

                    try:
                        result = future.result()

                        if "error" not in result or result.get("error") is None:
                            successful_uploads += 1
                            batch_successful += 1
                        else:
                            failed_uploads += 1
                            batch_failed += 1
                            logging.error(f"Failed: {file_path}: {result.get('error')}")

                    except Exception as e:
                        failed_uploads += 1
                        batch_failed += 1
                        logging.error(f"Exception processing {file_path}: {e}")

            # Save batch results
            batch_results.append({
                'batch_number': batch_num,
                'folder_name': folder_name,
                'total_files': len(batch_files),
                'successful': batch_successful,
                'failed': batch_failed
            })

            # Add delay between batches
            if batch_end < total_files:
                logging.info(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)

        # Save uploaded documents info to file
        self.save_upload_manifest(workspace_slug)

        # Return summary
        summary = {
            "total_files": total_files,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "batch_results": batch_results,
            "status": "completed",
            "manifest_file": f"upload_manifest_{workspace_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }

        logging.info(f"Upload Summary: {json.dumps(summary, indent=2)}")
        return summary

    def save_upload_manifest(self, workspace_slug: str):
        """Save manifest of uploaded documents"""
        manifest_file = f"upload_manifest_{workspace_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(manifest_file, 'w') as f:
            json.dump({
                'workspace': workspace_slug,
                'upload_date': datetime.now().isoformat(),
                'total_documents': len(self.uploaded_documents),
                'documents': self.uploaded_documents
            }, f, indent=2)
        
        logging.info(f"Upload manifest saved to: {manifest_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk upload documents to AnythingLLM")
    parser.add_argument("--base-url", default="http://localhost:3001", help="AnythingLLM base URL")
    parser.add_argument("--api-key", required=True, help="AnythingLLM API key")
    parser.add_argument("--directory", required=True, help="Directory containing documents")
    parser.add_argument("--workspace", required=True, help="Workspace slug")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent uploads")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between batches in seconds")
    parser.add_argument("--no-batch-folders", action="store_true", help="Don't create separate folders per batch")
    
    args = parser.parse_args()
    
    uploader = AnythingLLMUploader(args.base_url, args.api_key)
    
    # Test connection
    if not uploader.test_connection():
        logging.error("Failed to connect to AnythingLLM. Please check URL and API key.")
        return
    
    # Run bulk upload
    result = uploader.bulk_upload_with_folders(
        directory_path=args.directory,
        workspace_slug=args.workspace,
        max_workers=args.max_workers,
        batch_size=args.batch_size,
        delay_between_batches=args.delay,
        use_batch_folders=not args.no_batch_folders
    )
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
