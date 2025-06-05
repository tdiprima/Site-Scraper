import os


def remove_header(directory):
    header = """Search Text

Select Search Scope

Search This Site

Just This Site

Search SBU Website

SBU Website

Search
"""
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Check if header exists and remove it
            if content.startswith(header):
                new_content = content[len(header):].lstrip()
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                print(f"Header removed from {filename}")
            else:
                print(f"No header found in {filename}")


if __name__ == "__main__":
    directory = "/home/tdiprima/github/Site-Scraper/stonybrook_content"
    if os.path.isdir(directory):
        remove_header(directory)
    else:
        print("Invalid directory path")
