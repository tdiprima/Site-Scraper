import json
import sqlite3

conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

print("=== Verifying All RAG Settings ===")

# Check system config
cursor.execute("SELECT data FROM config")
config = json.loads(cursor.fetchone()[0])
rag = config["rag"]

print("System RAG settings:")
print(f"- top_k: {rag['top_k']} (initial retrieval)")
print(f"- relevance_threshold: {rag['relevance_threshold']}")
print(f"- reranking_model: {rag['reranking_model']}")
print(f"- top_k_reranker: {rag['top_k_reranker']} (final results)")

# Check your user settings
cursor.execute("SELECT settings FROM user WHERE email='tammy.diprima@stonybrook.edu'")
settings = json.loads(cursor.fetchone()[0])

print(f"\nYour user settings:")
print(f"- top_k: {settings['ui']['params']['top_k']}")
print(
    f"- relevance_threshold: {settings['ui']['params'].get('relevance_threshold', 'not set')}"
)

conn.close()

print("\n=== Analysis ===")
print(f"System top_k of {rag['top_k']} is actually GOOD!")
print("Here's why:")
print("1. It retrieves many candidates (1032) from the vector DB")
print("2. Your user top_k (50) limits this to 50 results")
print("3. The reranker then picks the best 20 from those 50")
print("\nThis is a good pipeline: wide initial search → user filter → smart reranking")

print("\n=== What to do now ===")
print("1. Restart Open WebUI to apply the config changes")
print("   - If using Docker: docker-compose restart")
print("   - If using systemd: sudo systemctl restart open-webui")
print("   - Or just stop and start it however you normally do")
print("\n2. After restart, test your queries:")
print("   - 'Tell me about the COVID-19 Data Commons'")
print("   - 'What do these files say about SOP'")
print("\n3. If it still doesn't work, we may need to:")
print("   - Disable the reranker temporarily")
print("   - Or increase your user top_k even higher (to 100+)")
