import os

folder = "openwebui_rag_docs"

for root, _, files in os.walk(folder):
    for fname in files:
        fpath = os.path.join(root, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        new_lines = [line for line in lines if line.strip().lower() not in {"on this page", "warning"}]
        with open(fpath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

