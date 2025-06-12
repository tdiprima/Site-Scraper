# Investigate further hidden filtering mechanisms in the Open WebUI configuration affecting retrieval.
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("=== Investigating the Real Problem ===")

# Check if there's another threshold mechanism
cursor.execute("SELECT id, settings FROM user WHERE email='tammy.diprima@stonybrook.edu'")
user_id, settings_json = cursor.fetchone()
settings = json.loads(settings_json)

print("Your current user params:")
print(json.dumps(settings['ui']['params'], indent=2))

# Let's check the system config more carefully
cursor.execute("SELECT * FROM config")
config = cursor.fetchone()
config_data = json.loads(config[1])

print("\nSystem RAG config:")
rag_config = config_data.get('rag', {})
for key, value in rag_config.items():
    if 'threshold' in key.lower() or 'score' in key.lower() or 'top' in key.lower() or 'rerank' in key.lower():
        print(f"  {key}: {value}")

print("\n=== The Real Issue ===")
print("Even with relevance_threshold: 0.0, your searches aren't working.")
print("This suggests:")
print("1. Open WebUI might be using top_k BEFORE checking threshold")
print("2. Your top_k of 10 might be too low if there are many irrelevant results")
print("3. There might be a reranking step that's filtering results")

print("\nNotice in the config:")
print(f"- System top_k: {rag_config.get('top_k', 'not set')} (very high!)")
print(f"- Your top_k: {settings['ui']['params'].get('top_k', 'not set')} (only 10)")
print(f"- Reranking enabled: {rag_config.get('reranking_model', 'not set')}")
print(f"- Top K after reranking: {rag_config.get('top_k_reranker', 'not set')}")

conn.close()

print("\n=== SOLUTION ===")
print("The problem is likely the reranking! It's taking your 10 results")
print("and then only keeping the top 3 after reranking.")
print("\nLet's increase your top_k to match the system setting...")
