"""Post-process a directory of scraped Markdown using CleanConfig."""

import logging
import re
from pathlib import Path

from .config import CleanConfig

log = logging.getLogger(__name__)


def clean_dir(directory: str | Path, cfg: CleanConfig) -> tuple[int, int]:
    """Apply the clean rules to every .md file. Returns (modified, deleted)."""
    patterns = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in cfg.remove_regex]
    modified = deleted = 0
    for path in sorted(Path(directory).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in cfg.delete_if_contains):
            path.unlink()
            deleted += 1
            log.info("Deleted %s", path.name)
            continue
        cleaned = text
        for pattern in patterns:
            cleaned = pattern.sub("", cleaned)
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            modified += 1
    return modified, deleted
