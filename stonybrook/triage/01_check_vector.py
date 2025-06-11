# Check the document count in the original ChromaDB collection.
import chromadb

client = chromadb.PersistentClient(path="/data/docker/volumes/open-webui/_data/vector_db")
# print(client.list_collections())  # Lists a gazillion collections including "8481691e-f9f2-4653-9643-4910e2e3499b".
collection = client.get_collection("8481691e-f9f2-4653-9643-4910e2e3499b")
print(collection.count())  # 47471
