# Investigate Open WebUI's configuration files and database tables to locate similarity threshold settings.
import json
import os
import sqlite3

print("=== Finding Open WebUI's RAG Configuration ===")

# Check the database for configuration
conn = sqlite3.connect("/app/backend/data/webui.db")
cursor = conn.cursor()

# Look for all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("All tables:", [t[0] for t in tables])

# Check for any config-related data
config_found = False
for table in tables:
    table_name = table[0]
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        columns = [description[0] for description in cursor.description]

        # Look for columns that might contain RAG settings
        if any(
            col in columns for col in ["config", "settings", "meta", "data", "params"]
        ):
            print(f"\n--- Checking {table_name} for RAG settings ---")
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            for row in rows:
                row_str = str(row).lower()
                if any(
                    term in row_str
                    for term in ["rag", "retriev", "threshold", "top_k", "similarity"]
                ):
                    print(f"Found potential config in {table_name}: {row}")
                    config_found = True
    except Exception as e:
        pass

conn.close()

# Check Open WebUI config files
print("\n=== Checking configuration files ===")
config_paths = [
    "/app/backend/config.json",
    "/app/backend/.env",
    "/app/backend/constants.py",
    "/app/backend/apps/rag/main.py",
]

for path in config_paths:
    if os.path.exists(path):
        print(f"\n--- {path} ---")
        try:
            with open(path, "r") as f:
                content = f.read()
                # Look for RAG-related settings
                for line in content.split("\n"):
                    if any(
                        term in line.lower()
                        for term in ["threshold", "top_k", "rag", "score", "similarity"]
                    ):
                        print(line.strip())
        except Exception as e:
            print(f"Could not read: {e}")

print("\n=== IMMEDIATE FIX ===")
print("Since searches ARE finding documents but with high distances,")
print("the issue is definitely the similarity threshold.")
print("\nOptions:")
print("1. Look in Open WebUI Settings UI for:")
print("   - 'Relevance Threshold' or 'Score Threshold'")
print("   - 'Minimum Similarity' or 'Similarity Threshold'")
print("   - Set it to 2.0 or higher (or 0.0 to disable)")
print("\n2. If no UI option, we'll need to modify the configuration directly")

print("\n=== Better Search Strategies ===")
print("Instead of searching for 'SOP', try:")
print("1. 'standard operating procedure SOP'")
print("2. 'what is the SOP procedure'")
print("3. 'SOP protocol guidelines'")
print("\nThese longer queries should produce better similarity scores!")
