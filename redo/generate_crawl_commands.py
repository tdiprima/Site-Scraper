"""
Input: ls -l | awk '{print $9}' > docs.txt
Output: crwl crawl "https://link" -o markdown -O "bmi_stonybrook_markdown/filename.md"
"""
import os
import subprocess

# Input file with filenames
INPUT_FILE = "docs.txt"
# Output directory for markdown files
OUTPUT_DIR = "bmi_stonybrook_markdown"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def reconstruct_url(filename):
    # Remove .md extension
    if not filename.endswith(".md"):
        return None
    base = filename[:-3]

    # Extract page number (e.g., _page_8)
    parts = base.split("_page_")
    if len(parts) != 2:
        return None
    path_part = parts[0]

    # Handle different prefixes
    if path_part.startswith("bmi_stonybrookmedicine_edu_"):
        domain = "https://bmi.stonybrookmedicine.edu"
        path = path_part[len("bmi_stonybrookmedicine_edu_"):]
    elif path_part.startswith("http:__bmi_stonybrookmedicine_edu_"):
        domain = "https://bmi.stonybrookmedicine.edu"
        path = path_part[len("http:__bmi_stonybrookmedicine_edu_"):]
    elif path_part.startswith("http:__www_stonybrookmedicine_edu_"):
        domain = "https://www.stonybrookmedicine.edu"
        path = path_part[len("http:__www_stonybrookmedicine_edu_"):]
    else:
        return None

    # Convert path underscores to slashes
    if path:
        url_path = path.replace("_", "/")
    else:
        url_path = ""

    # Construct full URL
    return f"{domain}/{url_path}".rstrip("/")


def generate_crawl_command(url, filename):
    if not url:
        return None
    output_path = os.path.join(OUTPUT_DIR, filename)
    return f'crwl crawl "{url}" -o markdown -O "{output_path}"'


def main():
    with open(INPUT_FILE, "r") as f:
        filenames = [line.strip() for line in f if line.strip()]

    commands = []
    for filename in filenames:
        url = reconstruct_url(filename)
        command = generate_crawl_command(url, filename)
        if command:
            commands.append(command)

    # Save commands to a bash script
    with open("run_crawl.sh", "w") as f:
        f.write("#!/bin/bash\n\n")
        for cmd in commands:
            f.write(f"{cmd}\n")

    print(f"Generated {len(commands)} crawl commands in run_crawl.sh")
    print("To execute, run: chmod +x run_crawl.sh && ./run_crawl.sh")
    print("Example commands:")
    for cmd in commands[:3]:  # Show first 3 as examples
        print(cmd)


if __name__ == "__main__":
    main()
