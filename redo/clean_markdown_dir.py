"""
All those links and short Markdown blocks are absolutely confusing your chunking + embedding.
Removed all the Markdown links and kept just the visible text.
"""
import re
from pathlib import Path


def clean_markdown_links(text):
    """Remove markdown links but preserve the visible text."""
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)


def clean_markdown_links_and_images(text):
    """
    Removes URLs from Markdown links and images,
    but keeps the visible text or alt text.
    
    [text](url) -> text
    ![alt](url) -> alt
    """
    # Remove images: ![alt](url) -> alt
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'\1', text)
    
    # Remove regular links: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    return text


def clean_all_markdown_files(directory_path):
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        print(f"❌ Not a directory: {directory_path}")
        return

    md_files = list(dir_path.glob("*.md"))

    if not md_files:
        print("⚠️ No Markdown files found.")
        return

    for md_file in md_files:
        original_text = md_file.read_text(encoding='utf-8')
        cleaned_text = clean_markdown_links_and_images(original_text)

        cleaned_filename = md_file.stem + "_cleaned.md"
        cleaned_path = md_file.with_name(cleaned_filename)
        cleaned_path.write_text(cleaned_text, encoding='utf-8')

        print(f"✅ Cleaned: {md_file.name} → {cleaned_filename}")


# Example usage:
clean_all_markdown_files("/path/to/your/markdown/folder")
