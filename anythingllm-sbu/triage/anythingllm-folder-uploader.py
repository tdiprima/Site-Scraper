"""
AnythingLLM Folder-Based Bulk Uploader
Uploads documents into organized folders for easy batch embedding
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
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'anythingllm_folder_upload_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)


class AnythingLLMFolderUploader:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json'
        }
        self.uploaded_documents = []
        
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

    def create_folder_structure(self, folder_name: str) -> Dict:
        """
        Create a folder in AnythingLLM
        Note: This might not be needed if folders are created automatically during upload
        """
        try:
            # This endpoint might vary - check your AnythingLLM API docs
            response = requests.post(
                f"{self.base_url}/api/v1/document/folder",
                headers=self.headers,
                json={"name": folder_name},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logging.info(f"Created folder: {folder_name}")
                return response.json()
            else:
                logging.warning(f"Folder creation returned: {response.status_code}")
                return {"status": "folder_might_exist"}
                
        except Exception as e:
            logging.warning(f"Folder creation exception (might be normal): {e}")
            return {"status": "folder_creation_skipped"}

    def upload_document_to_folder(self, file_path: str, folder_path: str) -> Dict:
        """
        Upload a document to a specific folder in AnythingLLM
        
        Args:
            file_path: Path to the file to upload
            folder_path: The folder path in AnythingLLM (e.g., "Batch_001" or "Batch_001/SubFolder")
        """
        try:
            # Prepare the file
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, mime_type)
                }
                
                # The folder parameter tells AnythingLLM where to put the document
                data = {
                    'folder': folder_path  # This is the key parameter
                }
                
                logging.info(f"Uploading {os.path.basename(file_path)} to folder: {folder_path}")

                response = requests.post(
                    f"{self.base_url}/api/v1/document/upload",
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=60  # Increased timeout for larger files
                )

                if response.status_code == 200:
                    result = response.json()
                    
                    # Track uploaded document info
                    if "documents" in result and result["documents"]:
                        doc_info = {
                            'file_path': file_path,
                            'document_id': result["documents"][0].get("id"),
                            'title': result["documents"][0].get("title"),
                            'folder': folder_path
                        }
                        self.uploaded_documents.append(doc_info)
                        logging.info(f"✓ Successfully uploaded: {os.path.basename(file_path)}")
                    
                    return result
                else:
                    error_msg = f"Status {response.status_code}: {response.text}"
                    logging.error(f"✗ Upload failed for {file_path}: {error_msg}")
                    return {"error": error_msg}

        except Exception as e:
            logging.error(f"✗ Error uploading {file_path}: {str(e)}")
            return {"error": str(e)}

    def get_all_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """Get all supported files from directory"""
        supported_extensions = self.get_supported_extensions()
        files = []
        
        path = Path(directory_path)
        if recursive:
            for ext in supported_extensions:
                files.extend([str(f) for f in path.rglob(f'*{ext}') if f.is_file() and f.stat().st_size > 0])
        else:
            for ext in supported_extensions:
                files.extend([str(f) for f in path.glob(f'*{ext}') if f.is_file() and f.stat().st_size > 0])
        
        return sorted(list(set(files)))  # Remove duplicates and sort

    def organize_files_by_size(self, files: List[str], docs_per_folder: int) -> List[Dict]:
        """
        Organize files into folder batches
        
        Returns:
            List of dicts with 'folder_name' and 'files' keys
        """
        batches = []
        
        for i in range(0, len(files), docs_per_folder):
            batch_files = files[i:i + docs_per_folder]
            batch_number = (i // docs_per_folder) + 1
            
            # Create descriptive folder name
            folder_name = f"Batch_{batch_number:03d}_{len(batch_files)}_docs"
            
            batches.append({
                'folder_name': folder_name,
                'files': batch_files,
                'batch_number': batch_number,
                'document_count': len(batch_files)
            })
        
        return batches

    def bulk_upload_with_folders(self, 
                                directory_path: str, 
                                workspace_slug: str,
                                docs_per_folder: int = 500,
                                max_workers: int = 3,
                                delay_between_folders: float = 2.0,
                                folder_prefix: str = "Batch") -> Dict:
        """
        Bulk upload documents organized into folders
        
        Args:
            directory_path: Source directory
            workspace_slug: Target workspace
            docs_per_folder: Number of documents per folder (default 500)
            max_workers: Concurrent upload threads
            delay_between_folders: Delay between folder uploads
            folder_prefix: Prefix for folder names
        """
        # Get all files
        files = self.get_all_files(directory_path)
        total_files = len(files)

        if total_files == 0:
            return {"error": "No supported files found"}

        logging.info(f"Found {total_files} files to upload")
        logging.info(f"Will create {(total_files + docs_per_folder - 1) // docs_per_folder} folders")

        # Organize files into folder batches
        folder_batches = self.organize_files_by_size(files, docs_per_folder)
        
        # Show upload plan
        logging.info("\nUpload Plan:")
        for batch in folder_batches:
            logging.info(f"  {batch['folder_name']}: {batch['document_count']} documents")
        
        # Confirm with user
        input("\nPress Enter to start upload (Ctrl+C to cancel)...")

        # Process each folder
        results = {
            "total_files": total_files,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "folders_created": len(folder_batches),
            "folder_results": []
        }

        for folder_batch in folder_batches:
            folder_name = folder_batch['folder_name']
            folder_files = folder_batch['files']
            
            logging.info(f"\n{'='*60}")
            logging.info(f"Processing {folder_name} ({len(folder_files)} files)")
            logging.info(f"{'='*60}")

            folder_successful = 0
            folder_failed = 0

            # Upload files to this folder in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                upload_futures = {
                    executor.submit(self.upload_document_to_folder, file_path, folder_name): file_path
                    for file_path in folder_files
                }

                # Process results with progress tracking
                completed = 0
                for future in as_completed(upload_futures):
                    completed += 1
                    file_path = upload_futures[future]

                    try:
                        result = future.result()

                        if "error" not in result or result.get("error") is None:
                            folder_successful += 1
                            results["successful_uploads"] += 1
                        else:
                            folder_failed += 1
                            results["failed_uploads"] += 1

                        # Progress update every 10 files
                        if completed % 10 == 0 or completed == len(folder_files):
                            logging.info(f"Progress: {completed}/{len(folder_files)} files processed")

                    except Exception as e:
                        folder_failed += 1
                        results["failed_uploads"] += 1
                        logging.error(f"Exception processing {file_path}: {e}")

            # Save folder results
            folder_result = {
                'folder_name': folder_name,
                'total_files': len(folder_files),
                'successful': folder_successful,
                'failed': folder_failed
            }
            results["folder_results"].append(folder_result)
            
            logging.info(f"\nFolder {folder_name} complete: {folder_successful} successful, {folder_failed} failed")

            # Delay between folders
            if folder_batch != folder_batches[-1]:
                logging.info(f"Waiting {delay_between_folders} seconds before next folder...")
                time.sleep(delay_between_folders)

        # Save manifest
        manifest_file = self.save_upload_manifest(workspace_slug, results)
        results["manifest_file"] = manifest_file

        # Print summary
        logging.info("\n" + "="*60)
        logging.info("UPLOAD COMPLETE")
        logging.info("="*60)
        logging.info(f"Total files: {results['total_files']}")
        logging.info(f"Successful: {results['successful_uploads']}")
        logging.info(f"Failed: {results['failed_uploads']}")
        logging.info(f"Folders created: {results['folders_created']}")
        logging.info(f"Manifest saved to: {manifest_file}")

        return results

    def save_upload_manifest(self, workspace_slug: str, results: Dict) -> str:
        """Save detailed manifest of the upload"""
        manifest_file = f"upload_manifest_{workspace_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        manifest = {
            'workspace': workspace_slug,
            'upload_date': datetime.now().isoformat(),
            'summary': results,
            'documents': self.uploaded_documents
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_file


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Upload documents to AnythingLLM organized in folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with 500 docs per folder
  python script.py --api-key YOUR_KEY --directory /path/to/docs --workspace my-workspace
  
  # Upload with 100 docs per folder
  python script.py --api-key YOUR_KEY --directory /path/to/docs --workspace my-workspace --docs-per-folder 100
  
  # Custom folder prefix
  python script.py --api-key YOUR_KEY --directory /path/to/docs --workspace my-workspace --folder-prefix "Markdown_Batch"
        """
    )
    
    parser.add_argument("--base-url", default="http://localhost:3001", help="AnythingLLM base URL")
    parser.add_argument("--api-key", required=True, help="AnythingLLM API key")
    parser.add_argument("--directory", required=True, help="Directory containing documents")
    parser.add_argument("--workspace", required=True, help="Workspace slug")
    parser.add_argument("--docs-per-folder", type=int, default=500, help="Documents per folder (default: 500)")
    parser.add_argument("--max-workers", type=int, default=3, help="Concurrent uploads (default: 3)")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between folders in seconds")
    parser.add_argument("--folder-prefix", default="Batch", help="Prefix for folder names")
    
    args = parser.parse_args()
    
    # Validate docs per folder
    if args.docs_per_folder < 1:
        parser.error("--docs-per-folder must be at least 1")
    
    uploader = AnythingLLMFolderUploader(args.base_url, args.api_key)
    
    # Test connection
    if not uploader.test_connection():
        logging.error("Failed to connect to AnythingLLM. Please check URL and API key.")
        return
    
    # Run bulk upload
    result = uploader.bulk_upload_with_folders(
        directory_path=args.directory,
        workspace_slug=args.workspace,
        docs_per_folder=args.docs_per_folder,
        max_workers=args.max_workers,
        delay_between_folders=args.delay,
        folder_prefix=args.folder_prefix
    )


if __name__ == "__main__":
    main()
