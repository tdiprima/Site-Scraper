# Deduplicate documents by source and create a new 'stonybrook_clean' ChromaDB collection.
import chromadb

client = chromadb.PersistentClient(path="/data/docker/volumes/open-webui/_data/vector_db")
collection = client.get_collection("8481691e-f9f2-4653-9643-4910e2e3499b")
docs = collection.get(include=["documents", "metadatas"])
unique_docs = {}
for doc, meta in zip(docs["documents"], docs["metadatas"]):
    source = meta.get("source", "")
    if source not in unique_docs:
        unique_docs[source] = (doc, meta)

try:
    client.delete_collection("stonybrook_clean")
    print("Deleted existing stonybrook_clean")
except ValueError:
    print("No existing stonybrook_clean, proceeding")

new_collection = client.create_collection("stonybrook_clean")
batch_size = 1000
total_docs = len(unique_docs)
for i in range(0, total_docs, batch_size):
    batch = list(unique_docs.values())[i:i + batch_size]
    new_collection.add(documents=[doc for doc, _ in batch], metadatas=[meta for _, meta in batch],
        ids=[f"doc_{j}" for j in range(i, i + len(batch))])
    print(f"Processed {i + len(batch)} of {total_docs} documents")

print(f"New collection count: {new_collection.count()}")
print(new_collection.peek(5)["metadatas"])
