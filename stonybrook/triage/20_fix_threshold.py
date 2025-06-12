import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("=== Fixing Your RAG Settings ===")

# Get your current settings
cursor.execute("SELECT id, settings FROM user WHERE email='tammy.diprima@stonybrook.edu'")
user_id, settings_json = cursor.fetchone()

# Parse current settings
settings = json.loads(settings_json)
print("Current params:", settings['ui']['params'])

# Update the params to include no threshold or a high threshold
settings['ui']['params']['relevance_threshold'] = 0.0  # No filtering
# Alternative: settings['ui']['params']['relevance_threshold'] = 2.0  # Allow high distances

# Also ensure top_k is reasonable
settings['ui']['params']['top_k'] = 20  # Increase from 10 to 20

print("New params:", settings['ui']['params'])

# Update the database
new_settings_json = json.dumps(settings)
cursor.execute("UPDATE user SET settings = ? WHERE id = ?", (new_settings_json, user_id))
conn.commit()

print("\n✅ SUCCESS! Your RAG settings have been updated:")
print(f"- top_k: 20 (increased from 10)")
print(f"- relevance_threshold: 0.0 (no filtering)")

conn.close()

print("\n🔄 IMPORTANT: You need to refresh Open WebUI:")
print("1. Log out and log back in")
print("   OR")
print("2. Clear your browser cache and refresh")
print("\nThen try your searches again!")

# Verify the change
conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()
cursor.execute("SELECT settings FROM user WHERE email='tammy.diprima@stonybrook.edu'")
updated_settings = json.loads(cursor.fetchone()[0])
print("\nVerification - New settings:")
print(json.dumps(updated_settings['ui']['params'], indent=2))
conn.close()
