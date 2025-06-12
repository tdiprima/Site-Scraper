import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("=== Checking Global vs User Settings ===")

# Get system config
cursor.execute("SELECT data FROM config")
config = json.loads(cursor.fetchone()[0])

print("SYSTEM DEFAULTS:")
print(f"- top_k: {config['rag']['top_k']} (good - casts wide net)")
print(f"- top_k_reranker: {config['rag']['top_k_reranker']} (✅ fixed to 20)")
print(f"- relevance_threshold: {config['rag']['relevance_threshold']}")

# Check what new users get by default
print("\n⚠️  PROBLEM: New users don't automatically get good settings!")
print("They'll get the defaults from the UI, which might be too restrictive.")

# Let's see what other users currently have
cursor.execute("SELECT name, email, settings FROM user")
users = cursor.fetchall()

print("\n=== Current User Settings ===")
problem_users = []
for name, email, settings_json in users:
    try:
        settings = json.loads(settings_json)
        params = settings.get('ui', {}).get('params', {})
        top_k = params.get('top_k', 'default')
        print(f"{name} ({email}): top_k = {top_k}")
        
        if top_k != 'default' and top_k < 50:
            problem_users.append((name, email))
    except:
        pass

if problem_users:
    print(f"\n⚠️  Found {len(problem_users)} users with potentially problematic settings:")
    for name, email in problem_users:
        print(f"  - {name} ({email})")

conn.close()

print("\n=== RECOMMENDATIONS ===")
print("1. The system reranker fix (top_k_reranker: 20) helps EVERYONE ✅")
print("\n2. But users might still have restrictive top_k settings.")
print("   Options:")
print("   a) Fix all existing users now (I can write a script)")
print("   b) Send an email telling users to increase their top_k to 50+")
print("   c) Wait and fix individually if they complain")
print("\n3. For future users, consider setting a better default in the UI code")
print("\nWould you like me to:")
print("- Fix all existing users' settings now?")
print("- Show you how to set better defaults for new users?")
print("- Both?")
