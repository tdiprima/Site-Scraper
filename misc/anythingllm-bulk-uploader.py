"""
AnythingLLM Bulk Document Uploader
This script handles bulk uploading of documents to AnythingLLM workspaces
python3 anythingllm-bulk-uploader.py --api-key $ANYTHINGLLM_API_KEY --directory /path/to/documents --workspace YOUR_WORKSPACE_SLUG --max-workers 16 --batch-size 200
"""

import os
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
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
    """
    A class to handle bulk document uploads to AnythingLLM
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the uploader with base URL and API key
        
        Args:
            base_url: The base URL of your AnythingLLM instance (e.g., 'http://localhost:3001')
            api_key: Your AnythingLLM API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        
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
    
    def upload_document(self, file_path: str) -> Dict:
        """
        Upload a single document to AnythingLLM
        
        Args:
            file_path: Path to the document
            
        Returns:
            Response from the API
        """
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                
                response = requests.post(
                    f"{self.base_url}/api/v1/document/upload",
                    headers=self.headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logging.error(f"Upload failed for {file_path}: {response.status_code} - {response.text}")
                    return {"error": response.text, "status_code": response.status_code}
                    
        except Exception as e:
            logging.error(f"Exception uploading {file_path}: {e}")
            return {"error": str(e)}
    
    def embed_document(self, document_id: str, workspace_slug: str) -> Dict:
        """
        Embed a document into a workspace
        
        Args:
            document_id: The ID of the uploaded document
            workspace_slug: The slug of the workspace
            
        Returns:
            Response from the API
        """
        try:
            payload = {
                "documentIds": [document_id]
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/workspace/{workspace_slug}/documents",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Embedding failed for document {document_id}: {response.status_code}")
                return {"error": response.text, "status_code": response.status_code}
                
        except Exception as e:
            logging.error(f"Exception embedding document {document_id}: {e}")
            return {"error": str(e)}
    
    def get_all_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Get all supported files from a directory
        
        Args:
            directory_path: Path to the directory
            recursive: Whether to search recursively
            
        Returns:
            List of file paths
        """
        supported_extensions = self.get_supported_extensions()
        files = []
        
        if recursive:
            for root, dirs, filenames in os.walk(directory_path):
                for filename in filenames:
                    if any(filename.lower().endswith(ext) for ext in supported_extensions):
                        files.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(directory_path):
                file_path = os.path.join(directory_path, filename)
                if os.path.isfile(file_path) and any(filename.lower().endswith(ext) for ext in supported_extensions):
                    files.append(file_path)
        
        return files
    
    def bulk_upload(self, directory_path: str, workspace_slug: str, 
                   max_workers: int = 5, batch_size: int = 100,
                   delay_between_batches: float = 1.0) -> Dict:
        """
        Bulk upload documents from a directory to a workspace
        
        Args:
            directory_path: Path to directory containing documents
            workspace_slug: The workspace to upload to
            max_workers: Maximum number of concurrent uploads
            batch_size: Number of files to process in each batch
            delay_between_batches: Delay in seconds between batches
            
        Returns:
            Summary of the upload process
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
        successful_embeds = 0
        failed_embeds = 0
        
        # Process files in batches
        for batch_start in range(0, total_files, batch_size):
            batch_end = min(batch_start + batch_size, total_files)
            batch_files = files[batch_start:batch_end]
            
            logging.info(f"Processing batch {batch_start//batch_size + 1}: files {batch_start + 1} to {batch_end}")
            
            # Upload files in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit upload tasks
                upload_futures = {
                    executor.submit(self.upload_document, file_path): file_path 
                    for file_path in batch_files
                }
                
                # Process upload results and submit embedding tasks
                embed_futures = {}
                
                for future in as_completed(upload_futures):
                    file_path = upload_futures[future]
                    
                    try:
                        result = future.result()
                        
                        if "error" not in result:
                            successful_uploads += 1
                            logging.info(f"Successfully uploaded: {file_path}")
                            
                            # Submit embedding task if upload was successful
                            if "id" in result:
                                embed_future = executor.submit(
                                    self.embed_document, 
                                    result["id"], 
                                    workspace_slug
                                )
                                embed_futures[embed_future] = result["id"]
                        else:
                            failed_uploads += 1
                            logging.error(f"Failed to upload: {file_path}")
                            
                    except Exception as e:
                        failed_uploads += 1
                        logging.error(f"Exception processing upload for {file_path}: {e}")
                
                # Process embedding results
                for future in as_completed(embed_futures):
                    document_id = embed_futures[future]
                    
                    try:
                        result = future.result()
                        
                        if "error" not in result:
                            successful_embeds += 1
                            logging.info(f"Successfully embedded document: {document_id}")
                        else:
                            failed_embeds += 1
                            logging.error(f"Failed to embed document: {document_id}")
                            
                    except Exception as e:
                        failed_embeds += 1
                        logging.error(f"Exception embedding document {document_id}: {e}")
            
            # Add delay between batches to avoid overwhelming the server
            if batch_end < total_files:
                logging.info(f"Waiting {delay_between_batches} seconds before next batch...")
                time.sleep(delay_between_batches)
        
        # Return summary
        summary = {
            "total_files": total_files,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "successful_embeds": successful_embeds,
            "failed_embeds": failed_embeds,
            "status": "completed"
        }
        
        logging.info(f"Upload Summary: {json.dumps(summary, indent=2)}")
        return summary

def main():
    """Main function to run the uploader"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk upload documents to AnythingLLM")
    parser.add_argument("--base-url", default="http://localhost:3001", help="AnythingLLM base URL")
    parser.add_argument("--api-key", required=True, help="AnythingLLM API key")
    parser.add_argument("--directory", required=True, help="Directory containing documents")
    parser.add_argument("--workspace", required=True, help="Workspace slug")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent uploads")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for uploads")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between batches in seconds")
    
    args = parser.parse_args()
    
    uploader = AnythingLLMUploader(args.base_url, args.api_key)
    
    # Test connection
    if not uploader.test_connection():
        logging.error("Failed to connect to AnythingLLM. Please check URL and API key.")
        return
    
    # Run bulk upload
    result = uploader.bulk_upload(
        directory_path=args.directory,
        workspace_slug=args.workspace,
        max_workers=args.max_workers,
        batch_size=args.batch_size,
        delay_between_batches=args.delay
    )
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
