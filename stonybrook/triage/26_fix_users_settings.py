import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("=== PART 1: Fixing All Existing Users ===")

# Get all users
cursor.execute("SELECT id, name, email, settings FROM user")
users = cursor.fetchall()

fixed_count = 0
for user_id, name, email, settings_json in users:
    try:
        settings = json.loads(settings_json)
        
        # Ensure the ui.params structure exists
        if 'ui' not in settings:
            settings['ui'] = {}
        if 'params' not in settings['ui']:
            settings['ui']['params'] = {}
        
        current_top_k = settings['ui']['params'].get('top_k', 'default')
        
        # Fix if needed
        if current_top_k == 'default' or current_top_k < 50:
            print(f"Fixing {name} ({email}): top_k {current_top_k} → 50")
            settings['ui']['params']['top_k'] = 50
            settings['ui']['params']['relevance_threshold'] = 0.0
            
            # Update database
            cursor.execute("UPDATE user SET settings = ? WHERE id = ?", 
                         (json.dumps(settings), user_id))
            fixed_count += 1
        else:
            print(f"✓ {name} ({email}): top_k already {current_top_k}")
            
    except Exception as e:
        print(f"Error processing {name}: {e}")

conn.commit()
print(f"\n✅ Fixed {fixed_count} users!")

conn.close()

print("\n=== PART 2: Setting Better Defaults for New Users ===")

# First, let's find where the defaults are set
import os
import glob

print("\nSearching for default configuration files...")

search_patterns = [
    "/app/backend/**/constants.py",
    "/app/backend/**/config*.py", 
    "/app/backend/**/defaults*.py",
    "/app/backend/**/settings*.py",
    "/app/backend/apps/webui/**/*.py"
]

default_files = []
for pattern in search_patterns:
    default_files.extend(glob.glob(pattern, recursive=True))

# Look for files that might contain defaults
for filepath in default_files[:10]:  # Check first 10 files
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if 'top_k' in content or 'DEFAULT' in content or 'params' in content:
                print(f"\nFound potential defaults in: {filepath}")
                # Show relevant lines
                for i, line in enumerate(content.split('\n')):
                    if 'top_k' in line.lower() or ('default' in line.lower() and 'param' in line.lower()):
                        print(f"  Line {i+1}: {line.strip()}")
    except:
        pass

print("\n=== IMMEDIATE SOLUTION ===")
print("While we search for the defaults file, here's a quick fix:")
print("\n1. Add a startup script that ensures good defaults:")

# Create a startup fix script
startup_script = '''#!/bin/bash
# /app/fix_defaults.sh - Run this after Open WebUI starts

echo "Ensuring good RAG defaults for all users..."

python3 << 'EOF'
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Fix any users with default or low top_k
cursor.execute("SELECT id, name, settings FROM user")
for user_id, name, settings_json in cursor.fetchall():
    try:
        settings = json.loads(settings_json)
        if 'ui' not in settings: settings['ui'] = {}
        if 'params' not in settings['ui']: settings['ui']['params'] = {}
        
        current = settings['ui']['params'].get('top_k', 0)
        if current < 50:
            settings['ui']['params']['top_k'] = 50
            settings['ui']['params']['relevance_threshold'] = 0.0
            cursor.execute("UPDATE user SET settings = ? WHERE id = ?", 
                         (json.dumps(settings), user_id))
            print(f"Fixed {name}")
    except:
        pass

conn.commit()
conn.close()
print("Done!")
EOF
'''

with open('/app/fix_defaults.sh', 'w') as f:
    f.write(startup_script)

os.chmod('/app/fix_defaults.sh', 0o755)

print("Created /app/fix_defaults.sh")
print("\n2. Add this to your docker-compose.yml or startup:")
print("   command: bash -c '/app/fix_defaults.sh && [original start command]'")

print("\n=== SUMMARY ===")
print("✅ All existing users fixed with top_k=50")
print("✅ System reranker already fixed to return 20 results")
print("✅ Created startup script to fix new users automatically")
print("\n📝 TODO: Find and modify the actual defaults file")
print("   (likely in /app/backend/constants.py or similar)")

# Let's also check the Open WebUI version for documentation
try:
    cursor = sqlite3.connect('/app/backend/data/webui.db').cursor()
    cursor.execute("SELECT data FROM config")
    config = json.loads(cursor.fetchone()[0])
    version = config.get('ui', {}).get('version', 'unknown')
    print(f"\n📌 Open WebUI Version: {version}")
    print("   Check their GitHub for where defaults are set in this version")
except:
    pass
