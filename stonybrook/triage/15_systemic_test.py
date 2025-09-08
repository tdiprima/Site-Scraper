# Systematically test random queries to check if retrieval issues are specific or systemic.

import chromadb

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

print("=== Testing if OTHER searches work ===")

# Test some random queries
test_queries = [
    "computer science programs",
    "undergraduate admissions",
    "research facilities",
    "student services",
    "faculty directory",
]

working_queries = 0
for query in test_queries:
    results = collection.query(query_texts=[query], n_results=3)
    if results["ids"][0]:
        working_queries += 1
        print(f"✓ '{query}' - Found {len(results['ids'][0])} results")
        print(
            f"  Best match: {results['metadatas'][0][0].get('source', 'Unknown')[:60]}..."
        )
    else:
        print(f"✗ '{query}' - No results")

print(f"\n{working_queries}/{len(test_queries)} queries working")

# Get a sample of what's actually in the collection
print("\n=== Random sample of documents ===")
sample = collection.get(limit=10, include=["documents", "metadatas"])
for i in range(min(3, len(sample["ids"]))):
    print(f"\nDoc {i+1}: {sample['metadatas'][i].get('source', 'Unknown')[:60]}...")
    print(f"Preview: {sample['documents'][i][:150]}...")

print("\n=== DECISION TIME ===")
if working_queries < 3:
    print("❌ Most queries failing - something is systemically wrong")
    print("   → Try reindexing OR recreate the collection")
else:
    print("✓ Other queries work - it's a specific issue")
    print("   → Reindexing might not help")
