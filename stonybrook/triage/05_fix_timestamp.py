# Fix invalid timestamp formats in the 'Stony Brook Clean' knowledge base entry.
import sqlite3
import time

# Fix the timestamp format for the Stony Brook Clean entry
conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Get the current timestamp as an integer
current_timestamp = int(time.time())

# Update the Stony Brook Clean entry to use integer timestamps
cursor.execute("""
    UPDATE knowledge 
    SET created_at = ?, updated_at = ? 
    WHERE id = '3c0b5e64-0cde-44f5-b785-3ed5ad8af070'
""", (current_timestamp, current_timestamp))

conn.commit()

# Verify the fix
cursor.execute("SELECT id, name, created_at, updated_at FROM knowledge")
knowledge_entries = cursor.fetchall()

print("Updated knowledge entries:")
for entry in knowledge_entries:
    print(f"  {entry[1]}: created_at={entry[2]} (type: {type(entry[2])}), updated_at={entry[3]} (type: {type(entry[3])})")

conn.close()

print("\n✓ Fixed timestamp format!")
print("Now try refreshing Open WebUI - it should work properly.")
