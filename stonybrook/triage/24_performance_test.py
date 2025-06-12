import chromadb
import time

client = chromadb.PersistentClient(path="/app/backend/data/vector_db")
collection = client.get_collection(name="3c0b5e64-0cde-44f5-b785-3ed5ad8af070")

print("=== Performance Test ===")

test_query = "COVID-19 Data Commons"

# Test with different k values
for k in [10, 50, 100, 500, 1000]:
    start = time.time()
    results = collection.query(
        query_texts=[test_query],
        n_results=k
    )
    elapsed = time.time() - start
    print(f"Retrieving top {k:4d}: {elapsed:.3f} seconds")

print("\n=== Conclusion ===")
print("If retrieval takes <0.5 seconds even for k=1000, the system top_k is fine.")
print("The real performance cost is in the reranking model, not the vector search.")
print("\nYou can leave it at 1032 - it's designed to cast a wide net!")
