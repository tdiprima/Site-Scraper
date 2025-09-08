# Extract current RAG threshold settings from Open WebUI's database configuration.
import json
import sqlite3

conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

print("=== Extracting RAG Configuration ===")

# Get the config table data
cursor.execute("SELECT * FROM config")
configs = cursor.fetchall()

for config in configs:
    try:
        config_data = json.loads(config[1])
        print("\n=== Main Config ===")
        print(json.dumps(config_data, indent=2))
    except Exception:
        pass

# Get user-specific settings
cursor.execute(
    "SELECT id, name, settings FROM user WHERE email='tammy.diprima@stonybrook.edu'"
)
user_data = cursor.fetchone()

if user_data:
    try:
        settings = json.loads(user_data[2])
        print("\n=== Your User Settings ===")
        print(json.dumps(settings, indent=2))

        # Look specifically for RAG params
        if "ui" in settings and "params" in settings["ui"]:
            print("\n=== Current RAG Parameters ===")
            print(f"top_k: {settings['ui']['params'].get('top_k', 'not set')}")
            print(
                f"score_threshold: {settings['ui']['params'].get('score_threshold', 'not set')}"
            )
            print(
                f"relevance_threshold: {settings['ui']['params'].get('relevance_threshold', 'not set')}"
            )
    except Exception:
        pass

conn.close()

print("\n=== SOLUTION ===")
print("Go to Open WebUI:")
print("1. Click your profile icon → Settings")
print("2. Go to 'Documents' or 'Interface' section")
print("3. Look for 'Top K' (should be 10 - that's good)")
print("4. Look for ANY threshold setting and set it to 0 or 2.0+")
print("\nIf you can't find threshold settings in the UI, we'll need to")
print("modify the database directly to add a higher threshold value.")
