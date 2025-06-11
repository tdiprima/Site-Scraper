import sqlite3

# Check if we can still access the database
try:
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()
    
    # Check knowledge entries
    cursor.execute("SELECT id, name, description FROM knowledge ORDER BY created_at DESC LIMIT 5")
    knowledge = cursor.fetchall()
    print("Recent knowledge entries:")
    for k in knowledge:
        print(f"  {k[1]}: {k[0]}")
    
    conn.close()
    print("\n✓ Database is accessible")
except Exception as e:
    print(f"Database error: {e}")
