import sqlite3
import chromadb
import time

# Connect to both databases
webui_conn = sqlite3.connect('/app/backend/data/webui.db')
webui_cursor = webui_conn.cursor()

# Connect to ChromaDB
client = chromadb.PersistentClient(path="/app/backend/data/vector_db")

# Get the deduplicated collection
collection_id = "3c0b5e64-0cde-44f5-b785-3ed5ad8af070"
collection = client.get_collection(name=collection_id)

print(f"Collection has {collection.count()} documents in ChromaDB")

# Get a sample of documents to populate the document table
# We'll get documents with their metadata
sample_size = min(100, collection.count())  # Get up to 100 docs
sample_data = collection.get(limit=sample_size, include=["metadatas"])

# Get the user_id from the knowledge table
webui_cursor.execute("SELECT user_id FROM knowledge WHERE id = ?", (collection_id,))
user_id = webui_cursor.fetchone()[0]
print(f"Using user_id: {user_id}")

# Insert documents into the document table
print(f"\nAdding document entries to Open WebUI database...")
current_timestamp = int(time.time())

for i, (doc_id, metadata) in enumerate(zip(sample_data['ids'], sample_data['metadatas'])):
    # Extract information from metadata
    source = metadata.get('source', 'Unknown source')
    title = metadata.get('title', source)
    filename = metadata.get('filename', source)
    
    # Create a document entry
    try:
        webui_cursor.execute("""
            INSERT INTO document (collection_name, name, title, filename, content, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            collection_id,  # collection_name is the knowledge ID
            doc_id,         # name is the document ID
            title,          # title
            filename,       # filename
            None,           # content (we don't store full content in this table)
            user_id,        # user_id
            current_timestamp  # timestamp
        ))
    except sqlite3.IntegrityError:
        # Document might already exist
        pass

webui_conn.commit()

# Check how many documents we added
webui_cursor.execute("SELECT COUNT(*) FROM document WHERE collection_name = ?", (collection_id,))
doc_count = webui_cursor.fetchone()[0]
print(f"✓ Added {doc_count} document entries to Open WebUI")

# Also check the original collection for comparison
webui_cursor.execute("SELECT COUNT(*) FROM document WHERE collection_name = ?", ("8481691e-f9f2-4653-9643-4910e2e3499b",))
original_doc_count = webui_cursor.fetchone()[0]
print(f"Original collection has {original_doc_count} document entries in Open WebUI")

webui_conn.close()

print("\n✓ Documents linked to knowledge base!")
print("Refresh the Open WebUI page - you should now see content in 'Stony Brook Clean'")

# If you want to see what sources were deduplicated:
print(f"\nSample of unique sources in the collection:")
sources = set()
all_metadata = collection.get(include=["metadatas"])['metadatas']
for meta in all_metadata[:10]:
    if 'source' in meta:
        sources.add(meta['source'])

for source in list(sources)[:5]:
    print(f"  - {source}")
