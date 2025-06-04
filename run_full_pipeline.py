import os
import re
import shutil
import subprocess
from pathlib import Path

# === Step 1: Run the scraper ===
SCRAPER_SCRIPT = "bmi_scraper.py"
RAW_DIR = "output_markdown"
CLEANED_DIR = "cleaned_markdown"

# Ensure clean start
if os.path.exists(RAW_DIR):
    print(f"Removing old '{RAW_DIR}' dir...")
    shutil.rmtree(RAW_DIR)
if os.path.exists(CLEANED_DIR):
    print(f"Removing old '{CLEANED_DIR}' dir...")
    shutil.rmtree(CLEANED_DIR)

print(f"\n[1/3] Running the web scraper...")
subprocess.run(["python3", SCRAPER_SCRIPT], check=True)


# === Step 2: Clean markdown files and save to CLEANED_DIR ===

def clean_markdown_links_and_images(text):
    # Remove images: ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    # Remove regular links: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text


print(f"\n[2/3] Cleaning markdown links and images...")

os.makedirs(CLEANED_DIR, exist_ok=True)
md_files = list(Path(RAW_DIR).glob("*.md"))
if not md_files:
    print(f"No Markdown files found in '{RAW_DIR}'!")
    exit(1)

for md_file in md_files:
    original_text = md_file.read_text(encoding='utf-8')
    cleaned_text = clean_markdown_links_and_images(original_text)
    cleaned_path = Path(CLEANED_DIR) / md_file.name
    cleaned_path.write_text(cleaned_text, encoding='utf-8')
    print(f"  Cleaned: {md_file.name} → {cleaned_path.name}")


# === Step 3: Strip header/footer from all files in CLEANED_DIR ===

def strip_header_footer(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # find header range
    start_idx = next((i for i, l in enumerate(lines) if "Skip to main content" in l), None)
    end_idx = None
    if start_idx is not None:
        end_idx = next((j for j in range(start_idx, len(lines)) if "Google Summer of Code" in lines[j]), start_idx)

    # find footer start
    footer_patterns = ("Stony Brook Medicine", "Stony Brook University Hospital", "Stony Brook Children's Hospital",)
    footer_idx = next((i for i, l in enumerate(lines) if any(l.startswith(p) for p in footer_patterns)), None)

    # build filtered lines
    new_lines = []
    for i, l in enumerate(lines):
        if start_idx is not None and start_idx <= i <= end_idx:
            continue
        if footer_idx is not None and i >= footer_idx:
            continue
        new_lines.append(l)

    # overwrite file
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)


print(f"\n[3/3] Stripping header/footer from cleaned files...")
cleaned_md_files = list(Path(CLEANED_DIR).glob("*.md"))
if not cleaned_md_files:
    print(f"No cleaned Markdown files found in '{CLEANED_DIR}'!")
    exit(1)

for md in cleaned_md_files:
    strip_header_footer(str(md))
    print(f"  Header/footer stripped: {md.name}")

print("\n✅ Pipeline complete! Cleaned files are in:", CLEANED_DIR)
