"""Upload scraped Markdown to an Open WebUI knowledge base.

Resumable: uploaded filenames are recorded in `<output_dir>/.crawl/uploaded.json`.
"""

import json
import logging
import time
from pathlib import Path

import requests

from .config import SiteConfig

log = logging.getLogger(__name__)


def upload_dir(site: SiteConfig, api_key: str, session: requests.Session | None = None):
    """Upload every .md file not uploaded yet. Returns (uploaded, failed)."""
    cfg = site.upload
    if not cfg.knowledge_id:
        raise ValueError("[upload] knowledge_id is required")
    base_url = cfg.base_url.rstrip("/")
    session = session or requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"

    progress_file = site.state_dir / "uploaded.json"
    done = json.loads(progress_file.read_text()) if progress_file.exists() else {}
    site.state_dir.mkdir(parents=True, exist_ok=True)

    uploaded = failed = 0
    for path in sorted(Path(site.output_dir).glob("*.md")):
        if path.name in done:
            continue
        try:
            with open(path, "rb") as f:
                resp = session.post(f"{base_url}/api/v1/files/", files={"file": f})
            resp.raise_for_status()
            file_id = resp.json()["id"]
            resp = session.post(
                f"{base_url}/api/v1/knowledge/{cfg.knowledge_id}/file/add",
                json={"file_id": file_id},
            )
            resp.raise_for_status()
        except (requests.RequestException, KeyError, ValueError) as e:
            log.warning("Failed %s: %s", path.name, e)
            failed += 1
            continue
        done[path.name] = file_id
        progress_file.write_text(json.dumps(done, indent=1))
        uploaded += 1
        log.info("Uploaded %s", path.name)
        time.sleep(cfg.delay)
    return uploaded, failed
