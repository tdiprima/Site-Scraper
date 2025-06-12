# Find the smoking gun
import chromadb

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

print("=== Testing SOP document retrieval ===")

# Check one of your known SOP documents
test_source = "www_stonybrook_edu_commcms_environmental-health-and-safety_programs_laboratory-safety_biological-safety_index.php.md"

# Get the actual document content
docs = collection.get(
    where={"source": test_source},
    include=["documents", "metadatas"]
)

if docs['ids']:
    print(f"\nFound document: {test_source}")
    content = docs['documents'][0]
    
    # Search for SOP in the content
    sop_count = content.upper().count("SOP")
    print(f"'SOP' appears {sop_count} times in this document")
    
    if sop_count > 0:
        # Find and show where SOP appears
        pos = content.upper().find("SOP")
        if pos >= 0:
            start = max(0, pos - 50)
            end = min(len(content), pos + 100)
            print(f"\nExample occurrence: ...{content[start:end]}...")

# Now test if searching for "SOP" finds this document
print("\n=== Testing search for 'SOP' ===")
results = collection.query(
    query_texts=["SOP"],
    n_results=10,
    where={"source": {"$in": [
        "www_stonybrook_edu_commcms_environmental-health-and-safety_programs_laboratory-safety_biological-safety_index.php.md",
        "www_stonybrook_edu_commcms_univ-senate_senate__senate-activity_capra-03-07-14.php.md"
    ]}}
)

print(f"Search found {len(results['ids'][0])} results")
for i, (distance, metadata) in enumerate(zip(results['distances'][0], results['metadatas'][0])):
    print(f"  {i+1}. Distance: {distance:.3f}, Source: {metadata.get('source', 'Unknown')[:60]}...")

print("\n=== DIAGNOSIS ===")
print("If SOP exists in documents but search doesn't find them, the issue is:")
print("1. Open WebUI might be using a different collection name/ID")
print("2. Open WebUI might have its own search logic that's filtering results")
print("3. The embedding model might not be working properly for short queries")

# Let's check what collections exist
print("\n=== All ChromaDB Collections ===")
try:
    all_collections = client.list_collections()
    for col in all_collections:
        print(f"- {col.name} ({col.count()} documents)")
except Exception as e:
    print(f"Error listing collections: {e}")
