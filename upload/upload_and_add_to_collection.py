import os
import time
from pathlib import Path

import requests

# ========== CONFIG ==========
token = os.environ.get("JWT_TOKEN")
knowledge_id = "bbbc10f3-b733-4252-b9ea-a5cf85f30870"
directory_path = "stonybrook_content"
uploaded_file_ids_path = "uploaded.txt"
added_to_collection_path = "added_to_collection.txt"
throttle_seconds = 1  # Pause between uploads (be kind to server!)


# ============================


def upload_file(token, file_path):
    url = "http://localhost:3000/api/v1/files/"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    files = {"file": open(file_path, "rb")}
    response = requests.post(url, headers=headers, files=files)
    files["file"].close()
    return response.json()


def add_file_to_knowledge(token, knowledge_id, file_id):
    url = f"http://localhost:3000/api/v1/knowledge/{knowledge_id}/file/add"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"file_id": file_id}
    return requests.post(url, headers=headers, json=data).json()


def load_progress(file_path):
    if Path(file_path).exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_progress(file_path, item):
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(str(item) + "\n")


# === MAIN ===
if not os.path.isdir(directory_path):
    raise ValueError(f"The directory {directory_path} does not exist")

# Load progress so far
uploaded_files = load_progress(uploaded_file_ids_path)  # stores file names
added_file_ids = load_progress(added_to_collection_path)  # stores file ids

for filename in os.listdir(directory_path):
    file_path = os.path.join(directory_path, filename)
    if not os.path.isfile(file_path):
        print(f"Skipping {file_path}, not a file.")
        continue
    if filename in uploaded_files:
        print(f"Already uploaded {filename}, skipping.")
        continue

    print(f"Uploading {file_path}...")
    try:
        result = upload_file(token, file_path)
        print(f"Upload result: {result}")
    except Exception as e:
        print(f"Error uploading {filename}: {e}")
        continue  # move on

    file_id = result.get("id")
    if not file_id:
        print(
            f"Warning: No id in response for {file_path}, skipping adding to collection."
        )
        continue

    save_progress(uploaded_file_ids_path, filename)  # Track uploaded filename

    if file_id in added_file_ids:
        print(f"Already added file_id {file_id} to collection, skipping.")
        continue

    try:
        response = add_file_to_knowledge(token, knowledge_id, file_id)
        print(f"Added to collection: {response}")
    except Exception as e:
        print(f"Error adding {file_id} to collection: {e}")
        continue

    save_progress(added_to_collection_path, file_id)  # Track added file_id

    time.sleep(throttle_seconds)  # Respectful pause

print("✅ Done! Safe to re-run if anything borks.")
