import requests
from collections import defaultdict
import os

# TODO: Configuration
BASE_URL = "http://localhost:3000"  # Your Open WebUI URL
API_KEY = os.environ.get("OPENWEBUI_API_KEY")  # Replace with your actual API key
expected_docs = 133
COLLECTION_ID = "2d823361-514e-4018-83ba-514c81b6fa98",  # Found in debug: "Open WebUI Docs"

# Headers
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def get_collections():
    """Fetch all collections"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/knowledge/", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching collections: {e}")
        return []


def get_collection_details(collection_id):
    """Get detailed information about a specific collection"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/knowledge/{collection_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching collection {collection_id}: {e}")
        return None


def get_documents_in_collection(collection_id):
    """Get all documents in a specific collection"""
    try:
        # Try different possible endpoints for documents
        endpoints_to_try = [
            f"/api/v1/files/",  # All files endpoint
            f"/api/v1/documents/",  # All documents endpoint
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
                print(f"   Trying {endpoint}: Status {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Found data at {endpoint}")
                    return data
                elif response.status_code != 404:
                    print(f"   Response: {response.text[:100]}")
            except Exception as e:
                print(f"   Error with {endpoint}: {e}")
                continue
        
        # If no endpoint works, return empty list
        print(f"   ❌ Could not find working documents endpoint for collection {collection_id}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching documents for collection {collection_id}: {e}")
        return []


def get_file_details(file_ids):
    """Get details for specific file IDs"""
    files_info = []
    print(f"   🔍 Fetching details for {len(file_ids)} files...")
    
    for i, file_id in enumerate(file_ids[:5]):  # Limit to first 5 for testing
        try:
            response = requests.get(f"{BASE_URL}/api/v1/files/{file_id}", headers=headers)
            if response.status_code == 200:
                file_data = response.json()
                files_info.append(file_data)
                print(f"      ✅ File {i+1}: {file_data.get('filename', 'Unknown')} ({file_data.get('meta', {}).get('size', 'Unknown')} bytes)")
            else:
                print(f"      ❌ File {i+1} ({file_id}): Status {response.status_code}")
        except Exception as e:
            print(f"      ❌ File {i+1} ({file_id}): Error {e}")
    
    if len(file_ids) > 5:
        print(f"      ... and {len(file_ids) - 5} more files")
    
    return files_info


def analyze_collections():
    """Main analysis function"""
    print("🔍 Starting Open WebUI Collection Audit")
    print("=" * 50)
    
    # Get all collections
    collections = get_collections()
    
    if not collections:
        print("❌ No collections found or error occurred")
        return
    
    print(f"📊 Found {len(collections)} total collections")
    print()
    
    # Your main collection IDs
    main_collection_ids = [
        COLLECTION_ID
    ]
    
    # Analyze each collection
    total_documents = 0
    main_collection_docs = 0
    individual_collections = []
    document_analysis = defaultdict(list)
    
    for collection in collections:
        collection_id = collection.get('id')
        collection_name = collection.get('name', 'Unnamed')
        
        # Get collection details
        details = get_collection_details(collection_id)
        if not details:
            continue
            
        # Get documents in this collection
        documents = get_documents_in_collection(collection_id)
        doc_count = len(documents) if documents else 0
        total_documents += doc_count
        
        print(f"📁 Collection: {collection_name}")
        print(f"   ID: {collection_id}")
        print(f"   Documents: {doc_count}")
        
        if collection_id in main_collection_ids:
            print("   ⭐ This is one of your MAIN collections")
            main_collection_docs += doc_count
        else:
            individual_collections.append({
                'id': collection_id,
                'name': collection_name,
                'doc_count': doc_count,
                'documents': documents or []
            })
        
        # Analyze document details
        if documents:
            print(f"   📄 Sample documents:")
            for i, doc in enumerate(documents[:3]):  # Show first 3 documents
                if isinstance(doc, dict):
                    doc_name = doc.get('name', doc.get('filename', 'Unknown'))
                    doc_size = doc.get('size', doc.get('file_size', 'Unknown size'))
                else:
                    doc_name = str(doc)
                    doc_size = 'Unknown size'
                    
                print(f"      - {doc_name} ({doc_size} bytes)")
                
                # Track document names to find duplicates
                document_analysis[doc_name].append(collection_id)
                
            if len(documents) > 3:
                print(f"      ... and {len(documents) - 3} more documents")
        
        # Also check if collection details include file_ids (from the debug output we saw)
        file_details = []
        if details and 'data' in details and 'file_ids' in details['data']:
            file_ids = details['data']['file_ids']
            print(f"   📄 Collection contains {len(file_ids)} file IDs")
            if file_ids:
                # Get details for the files
                file_details = get_file_details(file_ids)
                
                # Update document count based on actual files found
                if file_details:
                    doc_count = len(file_ids)  # Use the file_ids count as the real document count
                    total_documents += doc_count - len(documents or [])  # Adjust total
                    
                    if collection_id in main_collection_ids:
                        main_collection_docs = doc_count
                    else:
                        # Update the collection info
                        for coll in individual_collections:
                            if coll['id'] == collection_id:
                                coll['doc_count'] = doc_count
                                break
                
            if len(file_ids) != doc_count:
                print(f"   ⚠️  Collection data shows {len(file_ids)} file_ids but documents endpoint found {doc_count}")
        print()
    
    # Summary Analysis
    print("📈 SUMMARY ANALYSIS")
    print("=" * 50)
    print(f"Total collections: {len(collections)}")
    print(f"Main collection documents: {main_collection_docs}")
    print(f"Individual collections: {len(individual_collections)}")
    print(f"Total documents across all collections: {total_documents}")
    print()
    
    # Check for duplicates
    duplicates = {name: collections for name, collections in document_analysis.items() if len(collections) > 1}
    if duplicates:
        print("⚠️  DUPLICATE DOCUMENTS FOUND:")
        for doc_name, collection_ids in duplicates.items():
            print(f"   '{doc_name}' appears in {len(collection_ids)} collections:")
            for cid in collection_ids:
                coll_name = next((c['name'] for c in collections if c['id'] == cid), 'Unknown')
                print(f"      - {coll_name} ({cid})")
        print()
    
    # Analyze individual collections
    if individual_collections:
        print("🔍 INDIVIDUAL COLLECTION ANALYSIS:")
        single_doc_collections = [c for c in individual_collections if c['doc_count'] == 1]
        multi_doc_collections = [c for c in individual_collections if c['doc_count'] > 1]
        
        print(f"   Collections with 1 document: {len(single_doc_collections)}")
        print(f"   Collections with multiple documents: {len(multi_doc_collections)}")
        
        if single_doc_collections:
            print("   \n   🔸 Single-document collections (likely file-based):")
            for collection in single_doc_collections[:10]:  # Show first 10
                print(f"      - {collection['name']} (1 doc)")
            if len(single_doc_collections) > 10:
                print(f"      ... and {len(single_doc_collections) - 10} more")
        
        if multi_doc_collections:
            print("   \n   🔸 Multi-document collections:")
            for collection in multi_doc_collections:
                print(f"      - {collection['name']} ({collection['doc_count']} docs)")
    else:
        print("🔍 INDIVIDUAL COLLECTION ANALYSIS:")
        print("   No individual collections found - all documents are in main collections.")
        single_doc_collections = []
        multi_doc_collections = []
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 50)
    
    if main_collection_docs == expected_docs and len(individual_collections) == 0:
        print("✅ Everything looks correct! No action needed.")
    elif len(single_doc_collections) == expected_docs:
        print("🔄 It appears each of your N files was uploaded as a separate collection.")
        print("   This might be intentional if you want to query individual files separately.")
        print("   Or it might be an upload configuration issue.")
    elif duplicates:
        print("⚠️  You have duplicate documents across collections.")
        print("   Consider consolidating to avoid redundancy.")
    else:
        print("🤔 Mixed situation detected. Review the analysis above to determine next steps.")
    

if __name__ == "__main__":
    analyze_collections()
