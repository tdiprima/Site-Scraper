"""
python3 -m venv ~/qdrant-test-env
source ~/qdrant-test-env/bin/activate
"""

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

QDRANT_HOST = "10.100.0.1"
QDRANT_PORT = 6333
COLLECTION_NAME = "test-openwebui"

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Check if collection exists
if client.collection_exists(COLLECTION_NAME):
    print(f"Collection '{COLLECTION_NAME}' already exists")
    # Optionally delete and recreate for a clean test
    client.delete_collection(COLLECTION_NAME)
    print(f"Deleted existing collection '{COLLECTION_NAME}'")

# Create test collection
client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=768, distance=Distance.COSINE),
)
print(f"Created collection '{COLLECTION_NAME}'")

# Add dummy point
dummy_vector = np.random.rand(768).tolist()
client.upsert(
    collection_name=COLLECTION_NAME,
    points=[
        PointStruct(
            id=1, vector=dummy_vector, payload={"text": "This is a test document."}
        )
    ],
)
print("Added test point to collection")

# Search using the recommended query_points method
result = client.query_points(
    collection_name=COLLECTION_NAME, query=dummy_vector, limit=1
)

print("Search Result:", result)
