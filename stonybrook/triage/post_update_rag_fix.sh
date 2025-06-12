#!/bin/bash
# post_update_rag_fix.sh - Run this after every Open WebUI update
# Save this script outside the container (e.g., in your docker volumes)

echo "=== Open WebUI Post-Update RAG Fix ==="
echo "Running at: $(date)"

# Define the container name (adjust if yours is different)
CONTAINER_NAME="open-webui"
DB_PATH="/app/backend/data/webui.db"

# Create the SQL file with triggers
cat > /tmp/user_defaults_triggers.sql << 'EOF'
-- Drop existing triggers if they exist (to avoid errors)
DROP TRIGGER IF EXISTS set_user_defaults_on_insert;
DROP TRIGGER IF EXISTS fix_user_defaults_on_update;

-- Trigger for new users (especially OIDC)
CREATE TRIGGER set_user_defaults_on_insert
AFTER INSERT ON user
FOR EACH ROW
WHEN NEW.settings IS NULL OR NEW.settings = ''
BEGIN
    UPDATE user 
    SET settings = '{"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}'
    WHERE id = NEW.id;
END;

-- Trigger for when settings get cleared
CREATE TRIGGER fix_user_defaults_on_update  
AFTER UPDATE OF settings ON user
FOR EACH ROW
WHEN NEW.settings IS NULL OR NEW.settings = ''
BEGIN
    UPDATE user 
    SET settings = '{"ui": {"params": {"top_k": 50, "relevance_threshold": 0.0}}}'
    WHERE id = NEW.id;
END;

-- Also fix any existing users with bad settings
UPDATE user 
SET settings = json_set(
    COALESCE(settings, '{}'),
    '$.ui.params.top_k', 50,
    '$.ui.params.relevance_threshold', 0.0
)
WHERE settings IS NULL 
   OR settings = ''
   OR json_extract(settings, '$.ui.params.top_k') IS NULL
   OR json_extract(settings, '$.ui.params.top_k') < 50;

-- Show results
SELECT COUNT(*) as users_fixed FROM user 
WHERE json_extract(settings, '$.ui.params.top_k') = 50;
EOF

echo "1. Copying SQL file to container..."
docker cp /tmp/user_defaults_triggers.sql ${CONTAINER_NAME}:/tmp/

echo "2. Applying triggers and fixes..."
docker exec ${CONTAINER_NAME} sqlite3 ${DB_PATH} < /tmp/user_defaults_triggers.sql

echo "3. Verifying triggers are installed..."
docker exec ${CONTAINER_NAME} sqlite3 ${DB_PATH} "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE '%user_defaults%';"

echo "4. Checking current user settings..."
docker exec ${CONTAINER_NAME} sqlite3 ${DB_PATH} "SELECT COUNT(*) as total_users, COUNT(CASE WHEN json_extract(settings, '$.ui.params.top_k') >= 50 THEN 1 END) as users_with_good_top_k FROM user;"

echo ""
echo "✅ RAG defaults fix applied successfully!"
echo ""
echo "=== OPTIONAL: Add to your update workflow ==="
echo "1. Add this line to your docker-compose.yml under the open-webui service:"
echo "   volumes:"
echo "     - ./post_update_rag_fix.sh:/scripts/post_update_rag_fix.sh:ro"
echo ""
echo "2. After running 'docker-compose pull' and 'docker-compose up -d', run:"
echo "   docker exec open-webui /scripts/post_update_rag_fix.sh"
echo ""
echo "Or simply run this script from your host after each update!"

# Clean up
rm -f /tmp/user_defaults_triggers.sql
