import json
import os
import sqlite3

conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

print("=== PART 1: Fixing All Existing Users (Including OIDC) ===")

# Get all users
cursor.execute("SELECT id, name, email, settings FROM user")
users = cursor.fetchall()

fixed_count = 0
oidc_count = 0
error_count = 0

for user_id, name, email, settings_json in users:
    try:
        # Handle None or empty settings (common with OIDC users)
        if settings_json is None or settings_json == "":
            print(
                f"🔧 {name} ({email}): No settings found (OIDC user?) - Creating defaults"
            )
            settings = {"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}
            cursor.execute(
                "UPDATE user SET settings = ? WHERE id = ?",
                (json.dumps(settings), user_id),
            )
            oidc_count += 1
            continue

        # Try to parse existing settings
        try:
            settings = json.loads(settings_json)
        except json.JSONDecodeError:
            print(f"⚠️  {name} ({email}): Invalid JSON in settings - Creating defaults")
            settings = {"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}
            cursor.execute(
                "UPDATE user SET settings = ? WHERE id = ?",
                (json.dumps(settings), user_id),
            )
            error_count += 1
            continue

        # Ensure the ui.params structure exists
        if settings is None:
            settings = {}
        if "ui" not in settings:
            settings["ui"] = {}
        if "params" not in settings["ui"]:
            settings["ui"]["params"] = {}

        current_top_k = settings["ui"]["params"].get("top_k", "default")

        # Fix if needed
        if current_top_k == "default" or current_top_k < 50:
            print(f"Fixing {name} ({email}): top_k {current_top_k} → 50")
            settings["ui"]["params"]["top_k"] = 50
            settings["ui"]["params"]["relevance_threshold"] = 0.0

            # Update database
            cursor.execute(
                "UPDATE user SET settings = ? WHERE id = ?",
                (json.dumps(settings), user_id),
            )
            fixed_count += 1
        else:
            print(f"✓ {name} ({email}): top_k already {current_top_k}")

    except Exception as e:
        print(f"❌ Error processing {name} ({email}): {e}")
        error_count += 1

conn.commit()
print("\n✅ Summary:")
print(f"   - Fixed existing users: {fixed_count}")
print(f"   - Fixed OIDC users: {oidc_count}")
print(f"   - Errors encountered: {error_count}")
print(f"   - Total users processed: {len(users)}")

conn.close()

print("\n=== PART 2: Creating Startup Script for Future OIDC Users ===")

# Create a more robust startup fix script
startup_script = """#!/bin/bash
# /app/fix_oidc_defaults.sh - Run this periodically or on startup

echo "Ensuring good RAG defaults for all users (including OIDC)..."

python3 << 'EOF'
import sqlite3
import json
import time

def fix_user_settings():
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, name, email, settings FROM user")
    users = cursor.fetchall()
    
    fixed_count = 0
    
    for user_id, name, email, settings_json in users:
        try:
            # Initialize settings if None or empty
            if settings_json is None or settings_json == '':
                settings = {}
            else:
                try:
                    settings = json.loads(settings_json)
                except:
                    settings = {}
            
            # Ensure structure exists
            if 'ui' not in settings:
                settings['ui'] = {}
            if 'params' not in settings['ui']:
                settings['ui']['params'] = {}
            
            # Check and fix top_k
            current = settings['ui']['params'].get('top_k', 0)
            if current < 50:
                settings['ui']['params']['top_k'] = 50
                settings['ui']['params']['relevance_threshold'] = 0.0
                cursor.execute("UPDATE user SET settings = ? WHERE id = ?", 
                             (json.dumps(settings), user_id))
                fixed_count += 1
                print(f"Fixed {name} ({email})")
        except Exception as e:
            print(f"Error with {name}: {e}")
    
    conn.commit()
    conn.close()
    
    if fixed_count > 0:
        print(f"\\nFixed {fixed_count} users")
    else:
        print("All users have correct settings")

# Run the fix
fix_user_settings()

# Optionally, run continuously to catch new OIDC logins
if "--watch" in sys.argv:
    print("\\nWatching for new users...")
    while True:
        time.sleep(300)  # Check every 5 minutes
        fix_user_settings()
EOF
"""

with open("/app/fix_oidc_defaults.sh", "w") as f:
    f.write(startup_script)

os.chmod("/app/fix_oidc_defaults.sh", 0o755)

print("Created /app/fix_oidc_defaults.sh")

print("\n=== USAGE OPTIONS ===")
print("\n1. One-time fix (already done above)")
print("\n2. Add to startup in docker-compose.yml:")
print("   command: bash -c '/app/fix_oidc_defaults.sh && [original start command]'")
print("\n3. Run as a background watcher for new OIDC users:")
print("   nohup /app/fix_oidc_defaults.sh --watch > /app/logs/fix_oidc.log 2>&1 &")
print("\n4. Add as a cron job:")
print("   */5 * * * * /app/fix_oidc_defaults.sh >> /app/logs/fix_oidc.log 2>&1")

print("\n=== ADDITIONAL RECOMMENDATION ===")
print("For a permanent fix, you should modify the OIDC user creation code")
print("in Open WebUI to set proper defaults when creating new users.")
print("Look for files like:")
print("  - /app/backend/apps/webui/routers/auths.py")
print("  - /app/backend/apps/webui/models/users.py")
print("And ensure new users get created with proper default settings.")

# Let's also create a SQL trigger as a backup
print("\n=== CREATING SQL TRIGGER ===")
trigger_sql = """
-- This trigger ensures new users get proper defaults
-- Run this in your SQLite database

CREATE TRIGGER IF NOT EXISTS set_user_defaults_on_insert
AFTER INSERT ON user
FOR EACH ROW
WHEN NEW.settings IS NULL OR NEW.settings = ''
BEGIN
    UPDATE user 
    SET settings = '{"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}'
    WHERE id = NEW.id;
END;

-- Also create one for updates in case settings get cleared
CREATE TRIGGER IF NOT EXISTS fix_user_defaults_on_update  
AFTER UPDATE OF settings ON user
FOR EACH ROW
WHEN NEW.settings IS NULL OR NEW.settings = ''
BEGIN
    UPDATE user 
    SET settings = '{"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}'
    WHERE id = NEW.id;
END;
"""

with open("/app/user_defaults_triggers.sql", "w") as f:
    f.write(trigger_sql)

print("Created /app/user_defaults_triggers.sql")
print(
    "Apply with: sqlite3 /app/backend/data/webui.db < /app/user_defaults_triggers.sql"
)
