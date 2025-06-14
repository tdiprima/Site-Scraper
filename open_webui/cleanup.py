import re
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarkdownCleaner:
    def __init__(self, input_dir, output_dir=None):
        """
        Initialize the markdown cleaner.

        Args:
            input_dir: Directory containing markdown files to clean
            output_dir: Directory to save cleaned files (if None, overwrites originals)
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if output_dir else self.input_dir

        if not self.input_dir.exists():
            raise ValueError(f"Input directory {input_dir} does not exist")

        if output_dir and self.output_dir != self.input_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def clean_file(self, filepath):
        """Clean a single markdown file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            original_length = len(content)

            # 1. Convert metadata block to just URL comment
            # Look for the metadata block at the beginning
            metadata_pattern = r'^(Source:\s*(https://[^\n]+)\n(?:Scraped:[^\n]+\n)?(?:Depth:[^\n]+\n)?)'
            match = re.match(metadata_pattern, content, re.MULTILINE)

            if match:
                url = match.group(2)
                # Replace the metadata block with just the URL comment
                content = re.sub(metadata_pattern, f'<!-- {url} -->\n', content, count=1)
                logger.info(f"  ✓ Converted metadata to URL comment")

            # 2. Convert markdown links to just text
            # Pattern for markdown links: [text](url)
            link_pattern = r'\[([^\]]+)\]\([^)]+\)'
            links_found = len(re.findall(link_pattern, content))

            if links_found > 0:
                content = re.sub(link_pattern, r'\1', content)
                logger.info(f"  ✓ Removed {links_found} markdown links")

            # 3. Remove table of contents / navigation lists
            # Look for common TOC patterns
            toc_patterns = [
                # Pattern 1: Lists with anchors (like the example provided)
                r'(?:^|\n)(?:[-*+]\s+\[[^\]]+\]\(#[^)]+\)(?:\n\s*[-*+]\s+\[[^\]]+\]\(#[^)]+\))*)+',
                # Pattern 2: Simple anchor lists
                r'(?:^|\n)(?:[-*+]\s+<a[^>]+href="#[^"]+[^<]+</a>(?:\n\s*[-*+]\s+<a[^>]+href="#[^"]+[^<]+</a>)*)+',
                # Pattern 3: Numbered lists with anchors
                r'(?:^|\n)(?:\d+\.\s+\[[^\]]+\]\(#[^)]+\)(?:\n\s*\d+\.\s+\[[^\]]+\]\(#[^)]+\))*)+',
            ]

            toc_removed = False
            for pattern in toc_patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                if matches:
                    # Remove from last to first to preserve indices
                    for match in reversed(matches):
                        # Check if this looks like a TOC (has multiple items)
                        toc_text = match.group(0)
                        if toc_text.count('\n') >= 2:  # At least 3 items
                            content = content[:match.start()] + content[match.end():]
                            toc_removed = True

            if toc_removed:
                logger.info(f"  ✓ Removed table of contents")

            # 4. Clean up any HTML links that might remain
            # Pattern for HTML links: <a href="...">text</a>
            html_link_pattern = r'<a[^>]+href=[^>]+>([^<]+)</a>'
            html_links_found = len(re.findall(html_link_pattern, content))

            if html_links_found > 0:
                content = re.sub(html_link_pattern, r'\1', content)
                logger.info(f"  ✓ Removed {html_links_found} HTML links")

            # 5. Clean up excessive whitespace
            # Remove multiple consecutive blank lines
            content = re.sub(r'\n{3,}', '\n\n', content)

            # Remove trailing whitespace from lines
            lines = [line.rstrip() for line in content.split('\n')]
            content = '\n'.join(lines)

            # Ensure file ends with single newline
            content = content.strip() + '\n'

            # Save the cleaned content
            output_path = self.output_dir / filepath.name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Report reduction
            new_length = len(content)
            reduction = ((original_length - new_length) / original_length * 100) if original_length > 0 else 0
            logger.info(f"  ✓ Reduced size by {reduction:.1f}% ({original_length} → {new_length} chars)")

            return True

        except Exception as e:
            logger.error(f"  ✗ Error cleaning {filepath}: {e}")
            return False

    def clean_all(self):
        """Clean all markdown files in the input directory"""
        logger.info("=" * 60)
        logger.info(f"Cleaning markdown files in: {self.input_dir}")
        if self.output_dir != self.input_dir:
            logger.info(f"Output directory: {self.output_dir}")
        else:
            logger.info("Overwriting original files")
        logger.info("=" * 60)

        # Find all markdown files
        md_files = list(self.input_dir.glob("*.md"))

        if not md_files:
            logger.warning("No markdown files found!")
            return

        logger.info(f"Found {len(md_files)} markdown files to clean\n")

        successful = 0
        failed = 0

        for md_file in md_files:
            logger.info(f"Processing: {md_file.name}")
            if self.clean_file(md_file):
                successful += 1
            else:
                failed += 1
            logger.info("")  # Empty line for readability

        # Summary
        logger.info("=" * 60)
        logger.info("Cleaning complete!")
        logger.info(f"✓ Successfully cleaned: {successful} files")
        if failed > 0:
            logger.info(f"✗ Failed: {failed} files")
        logger.info("=" * 60)


def main():
    # Configuration
    INPUT_DIR = "openwebui_docs"  # Directory with your scraped files
    OUTPUT_DIR = None  # Set to None to overwrite originals, or specify a different directory

    # To save cleaned files to a new directory:
    # OUTPUT_DIR = "openwebui_docs_cleaned"

    # Create and run cleaner
    cleaner = MarkdownCleaner(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR
    )

    cleaner.clean_all()


if __name__ == "__main__":
    main()
