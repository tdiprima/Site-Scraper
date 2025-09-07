# Delete the original duplicated collection from both ChromaDB and the SQLite DB.
import sqlite3

import chromadb

print("=== Cleaning up old collection ===")

# Connect to ChromaDB
client = chromadb.PersistentClient(path="/app/backend/data/vector_db")

# The original collection with duplicates
old_collection_id = "8481691e-f9f2-4653-9643-4910e2e3499b"

# First, let's verify what we're about to delete
try:
    old_collection = client.get_collection(name=old_collection_id)
    doc_count = old_collection.count()
    print(
        f"Original collection 'stonybrook' has {doc_count} documents (with duplicates)"
    )

    # Delete the collection from ChromaDB
    client.delete_collection(name=old_collection_id)
    print("✓ Deleted old collection from ChromaDB")
except Exception as e:
    print(f"Collection might already be deleted: {e}")

# Also remove it from Open WebUI's database
conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

# Delete from knowledge table
cursor.execute("DELETE FROM knowledge WHERE id = ?", (old_collection_id,))
print(f"✓ Removed {cursor.rowcount} entries from knowledge table")

# Delete from document table (if any)
cursor.execute("DELETE FROM document WHERE collection_name = ?", (old_collection_id,))
print(f"✓ Removed {cursor.rowcount} entries from document table")

conn.commit()

# Show remaining knowledge bases
cursor.execute("SELECT id, name, description FROM knowledge")
remaining = cursor.fetchall()
print("\n=== Remaining knowledge bases ===")
for kb in remaining:
    print(f"- {kb[1]}: {kb[2]}")

conn.close()

# Check ChromaDB collections
print("\n=== ChromaDB collections ===")
collections = client.list_collections()
for col in collections:
    print(f"- {col.name} ({col.count()} documents)")

print("\n✓ Cleanup complete!")
print(
    "Your 'Stony Brook Clean' knowledge base is the only one remaining for Stony Brook content."
)
