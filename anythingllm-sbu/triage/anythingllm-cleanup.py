"""
AnythingLLM Document Cleanup Script
This script helps delete documents from AnythingLLM workspaces
"""

import requests
import logging
from typing import List, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class AnythingLLMCleaner:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_workspace_documents(self, workspace_slug: str) -> List[Dict]:
        """Get all documents in a workspace"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/workspace/{workspace_slug}/documents",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('documents', [])
            else:
                logging.error(f"Failed to get documents: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"Error getting documents: {e}")
            return []
    
    def delete_document(self, workspace_slug: str, document_id: str) -> bool:
        """Delete a single document from a workspace"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/workspace/{workspace_slug}/document/{document_id}",
                headers=self.headers,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logging.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def delete_all_documents(self, workspace_slug: str) -> Dict:
        """Delete all documents from a workspace"""
        documents = self.get_workspace_documents(workspace_slug)
        
        if not documents:
            return {"message": "No documents found to delete"}
        
        deleted_count = 0
        failed_count = 0
        
        for doc in documents:
            doc_id = doc.get('id')
            if doc_id:
                if self.delete_document(workspace_slug, doc_id):
                    deleted_count += 1
                    logging.info(f"Deleted document: {doc.get('title', doc_id)}")
                else:
                    failed_count += 1
                    logging.error(f"Failed to delete document: {doc.get('title', doc_id)}")
        
        return {
            "total_documents": len(documents),
            "deleted": deleted_count,
            "failed": failed_count
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up documents from AnythingLLM")
    parser.add_argument("--base-url", default="http://localhost:3001", help="AnythingLLM base URL")
    parser.add_argument("--api-key", required=True, help="AnythingLLM API key")
    parser.add_argument("--workspace", required=True, help="Workspace slug")
    parser.add_argument("--confirm", action="store_true", help="Confirm deletion without prompt")
    
    args = parser.parse_args()
    
    cleaner = AnythingLLMCleaner(args.base_url, args.api_key)
    
    # Get document count first
    documents = cleaner.get_workspace_documents(args.workspace)
    
    if not documents:
        print("No documents found in the workspace.")
        return
    
    print(f"Found {len(documents)} documents in workspace '{args.workspace}'")
    
    if not args.confirm:
        response = input("Are you sure you want to delete all documents? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return
    
    # Delete all documents
    result = cleaner.delete_all_documents(args.workspace)
    print(f"\nDeletion complete:")
    print(f"  Deleted: {result['deleted']}")
    print(f"  Failed: {result['failed']}")


if __name__ == "__main__":
    main()
