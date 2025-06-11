import chromadb
import sqlite3

print("=== Working with ChromaDB Collections ===")
client = chromadb.PersistentClient(path="/app/backend/data/vector_db")

original_knowledge_id = "8481691e-f9f2-4653-9643-4910e2e3499b"
new_knowledge_id = "3c0b5e64-0cde-44f5-b785-3ed5ad8af070"

try:
    # Get the original collection
    print(f"Getting collection: {original_knowledge_id}")
    original = client.get_collection(name=original_knowledge_id)
    print(f"✓ Found collection with {original.count()} documents")
    
    # Get all data at once (ChromaDB handles large fetches well)
    print("\nFetching all documents for deduplication...")
    all_data = original.get(include=["documents", "metadatas", "embeddings"])
    
    print(f"Total documents fetched: {len(all_data['ids'])}")
    
    # Deduplicate by source
    print("\nDeduplicating by source...")
    unique_docs = {}
    
    for i in range(len(all_data['ids'])):
        doc_id = all_data['ids'][i]
        document = all_data['documents'][i]
        metadata = all_data['metadatas'][i]
        embedding = all_data['embeddings'][i] if all_data['embeddings'] is not None else None
        
        # Use source from metadata, or document ID if no source
        source = metadata.get('source', doc_id)
        
        if source not in unique_docs:
            unique_docs[source] = {
                'id': doc_id,
                'document': document,
                'metadata': metadata,
                'embedding': embedding
            }
    
    print(f"✓ Deduplicated from {len(all_data['ids'])} to {len(unique_docs)} unique documents")
    
    # Delete existing collection if it exists
    try:
        existing = client.get_collection(name=new_knowledge_id)
        print(f"\nDeleting existing collection: {new_knowledge_id}")
        client.delete_collection(name=new_knowledge_id)
    except:
        print(f"\nNo existing collection to delete")
    
    # Create new collection
    print(f"\nCreating new collection: {new_knowledge_id}")
    new_collection = client.create_collection(name=new_knowledge_id)
    
    # Prepare data for batch insertion
    all_unique_docs = list(unique_docs.values())
    batch_size = 500  # Smaller batches for stability
    
    print(f"\nAdding {len(all_unique_docs)} unique documents...")
    
    for i in range(0, len(all_unique_docs), batch_size):
        batch = all_unique_docs[i:i + batch_size]
        
        # Prepare batch data
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        has_embeddings = False
        
        for j, doc in enumerate(batch):
            ids.append(f"doc_{i+j}")
            documents.append(doc['document'])
            metadatas.append(doc['metadata'])
            
            if doc['embedding'] is not None:
                embeddings.append(doc['embedding'])
                has_embeddings = True
        
        # Add to collection
        if has_embeddings and len(embeddings) == len(ids):
            new_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        else:
            new_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        
        # Progress update
        current = min(i + batch_size, len(all_unique_docs))
        if current % 2000 == 0 or current == len(all_unique_docs):
            print(f"  Progress: {current}/{len(all_unique_docs)} documents ({current*100//len(all_unique_docs)}%)")
    
    # Verify the new collection
    final_count = new_collection.count()
    print(f"\n✓ Successfully created deduplicated collection!")
    print(f"  Collection name: {new_knowledge_id}")
    print(f"  Document count: {final_count}")
    
    # Verify it's in the database
    conn = sqlite3.connect("/app/backend/data/vector_db/chroma.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM collections WHERE name = ?", (new_knowledge_id,))
    result = cursor.fetchone()
    if result:
        print(f"  Internal ID: {result[0]}")
        print(f"  ✓ Collection is properly registered in ChromaDB")
    conn.close()
    
    # Show sample of deduplicated sources
    print(f"\nSample of unique sources:")
    sample_sources = list(unique_docs.keys())[:5]
    for source in sample_sources:
        print(f"  - {source}")
    
    print(f"\n🎉 SUCCESS! 'Stony Brook Clean' should now appear in Open WebUI!")
    print("Please refresh your Open WebUI page to see it in the Knowledge section.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
