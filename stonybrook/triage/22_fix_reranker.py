# Adjust reranking settings in Open WebUI to ensure enough results pass through after reranking.
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("=== FIXING THE RERANKER ISSUE ===")

# First, let's see the config table structure
cursor.execute("PRAGMA table_info(config)")
columns = cursor.fetchall()
print("Config table columns:", [col[1] for col in columns])

# Get the config properly
cursor.execute("SELECT * FROM config")
config_row = cursor.fetchone()
print(f"Config row has {len(config_row)} columns")

# Find which column has the JSON data
config_json = None
config_id = config_row[0]

# Try each column to find the JSON
for i, value in enumerate(config_row):
    if isinstance(value, str) and value.startswith('{'):
        config_json = value
        print(f"Found JSON config in column {i}")
        break

if config_json:
    config = json.loads(config_json)
    
    # Show current problematic setting
    print(f"\nCurrent top_k_reranker: {config['rag']['top_k_reranker']} (TOO LOW!)")
    
    # Fix it
    config['rag']['top_k_reranker'] = 20  # Increase from 3 to 20
    print(f"New top_k_reranker: {config['rag']['top_k_reranker']}")
    
    # Also update your user top_k to be higher
    cursor.execute("SELECT id, settings FROM user WHERE email='tammy.diprima@stonybrook.edu'")
    user_id, settings_json = cursor.fetchone()
    settings = json.loads(settings_json)
    settings['ui']['params']['top_k'] = 50  # Increase to 50
    
    # Save both changes - update the correct column
    cursor.execute("UPDATE config SET data = ? WHERE id = ?", (json.dumps(config), config_id))
    cursor.execute("UPDATE user SET settings = ? WHERE id = ?", (json.dumps(settings), user_id))
    conn.commit()
    
    print("\n✅ FIXED! Changes made:")
    print("- top_k_reranker: 3 → 20 (system will now return 20 results after reranking)")
    print("- your top_k: 20 → 50 (gives reranker more candidates to choose from)")
    
    conn.close()
    
    print("\n🔄 CRITICAL: You MUST restart Open WebUI for system config changes:")
    print("1. Stop Open WebUI (docker-compose down or systemctl stop)")
    print("2. Start it again")
    print("3. Try your searches - they should work now!")
else:
    print("ERROR: Could not find JSON config data")
    conn.close()
