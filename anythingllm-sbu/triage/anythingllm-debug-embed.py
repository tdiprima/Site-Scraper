"""
AnythingLLM Embedding Debug Script
Tests different embedding approaches
"""

import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG)


class EmbeddingDebugger:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def test_embed_single(self, workspace_slug: str, document_id: str):
        """Test embedding a single document"""
        print(f"\nTesting single document embedding...")
        
        # Try different payload formats
        payloads = [
            {"documentIds": [document_id]},
            {"documents": [document_id]},
            {"document_ids": [document_id]},
            {"ids": [document_id]}
        ]
        
        for i, payload in enumerate(payloads):
            print(f"\nAttempt {i+1} with payload: {json.dumps(payload)}")
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/workspace/{workspace_slug}/documents",
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                # Try to parse response
                try:
                    json_response = response.json()
                    print(f"JSON Response: {json.dumps(json_response, indent=2)}")
                except:
                    print(f"Raw Response: {response.text[:500]}...")
                    
            except Exception as e:
                print(f"Error: {e}")
    
    def check_workspace_api(self, workspace_slug: str):
        """Check workspace endpoints"""
        print(f"\nChecking workspace API endpoints...")
        
        endpoints = [
            f"/api/v1/workspace/{workspace_slug}",
            f"/api/v1/workspace/{workspace_slug}/documents",
            f"/api/v1/workspaces/{workspace_slug}/documents",
            f"/api/workspace/{workspace_slug}/documents"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=self.headers,
                    timeout=10
                )
                print(f"\nGET {endpoint}: {response.status_code}")
                if response.status_code == 200:
                    print("Found working endpoint!")
                    
            except Exception as e:
                print(f"GET {endpoint}: Error - {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug AnythingLLM embedding")
    parser.add_argument("--base-url", default="http://localhost:3001")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--document-id", help="Test with a specific document ID")
    
    args = parser.parse_args()
    
    debugger = EmbeddingDebugger(args.base_url, args.api_key)
    
    # Check workspace endpoints
    debugger.check_workspace_api(args.workspace)
    
    # Test embedding if document ID provided
    if args.document_id:
        debugger.test_embed_single(args.workspace, args.document_id)
    else:
        print("\nProvide a --document-id to test embedding")


if __name__ == "__main__":
    main()
