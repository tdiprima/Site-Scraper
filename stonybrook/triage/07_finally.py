# Recreate deduplicated ChromaDB collection without embeddings to resolve mismatch issues.
import sqlite3
import time

import chromadb

print("=== Fixing embedding dimension mismatch ===")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="/app/backend/data/vector_db")

# Delete the problematic collection
collection_id = "3c0b5e64-0cde-44f5-b785-3ed5ad8af070"
print("Deleting collection with mismatched embeddings...")
try:
    client.delete_collection(name=collection_id)
    print("✓ Deleted existing collection")
except Exception:
    print("Collection already deleted")

# Get the original collection data WITHOUT embeddings
original_collection = client.get_collection(name="8481691e-f9f2-4653-9643-4910e2e3499b")
print("\nFetching documents from original collection...")
all_data = original_collection.get(include=["documents", "metadatas"])

# Deduplicate again
print("Deduplicating documents...")
unique_docs = {}
for i in range(len(all_data["ids"])):
    doc_id = all_data["ids"][i]
    document = all_data["documents"][i]
    metadata = all_data["metadatas"][i]

    source = metadata.get("source", doc_id)
    if source not in unique_docs:
        unique_docs[source] = {"document": document, "metadata": metadata}

print(f"✓ Deduplicated to {len(unique_docs)} unique documents")

# Create new collection WITHOUT specifying embeddings
# This will let Open WebUI generate them with the correct model
print("\nCreating new collection without embeddings...")
new_collection = client.create_collection(name=collection_id)

# Add documents in batches without embeddings
batch_size = 500
all_unique_docs = list(unique_docs.values())

print(f"Adding {len(all_unique_docs)} documents...")
for i in range(0, len(all_unique_docs), batch_size):
    batch = all_unique_docs[i : i + batch_size]

    ids = [f"doc_{i+j}" for j in range(len(batch))]
    documents = [d["document"] for d in batch]
    metadatas = [d["metadata"] for d in batch]

    # Add WITHOUT embeddings - let ChromaDB generate them
    new_collection.add(ids=ids, documents=documents, metadatas=metadatas)

    if (i + batch_size) % 2000 == 0:
        print(
            f"  Progress: {min(i + batch_size, len(all_unique_docs))}/{len(all_unique_docs)} documents"
        )

print(f"\n✓ Collection recreated with {new_collection.count()} documents")

# Test the collection now
print("\n=== Testing the fixed collection ===")
test_query = "Stony Brook University programs"
try:
    results = new_collection.query(query_texts=[test_query], n_results=3)
    print(f"✓ Query successful! Found {len(results['ids'][0])} results")
    print("\nThe knowledge base should now work properly in Open WebUI!")
except Exception as e:
    print(f"Query error: {e}")

# Update the document table entry
conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

current_timestamp = int(time.time())
cursor.execute(
    """
    UPDATE document 
    SET title = ?,
        filename = ?,
        content = ?,
        timestamp = ?
    WHERE collection_name = ?
""",
    (
        f"Stony Brook University - Deduplicated ({new_collection.count()} documents)",
        "stonybrook_deduplicated.md",
        f"Deduplicated knowledge base containing {new_collection.count()} unique documents from Stony Brook University website",
        current_timestamp,
        collection_id,
    ),
)

conn.commit()
conn.close()

print("\n✓ Updated document metadata")
print("\n🎉 DONE! Your 'Stony Brook Clean' knowledge base should now work properly!")
print("\nTo use it:")
print("1. Go to a chat in Open WebUI")
print("2. Click the attachment icon and select 'Stony Brook Clean' from Knowledge")
print("3. Ask questions about Stony Brook University")
