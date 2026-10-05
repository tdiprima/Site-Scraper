"""Command-line entry point: site-scraper {crawl,clean,upload} CONFIG"""

import argparse
import logging
import os
import sys

from .clean import clean_dir
from .config import load_config
from .crawler import Crawler
from .upload import upload_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="site-scraper", description="Crawl a website into clean Markdown."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in [
        ("crawl", "crawl the site and save each page as Markdown"),
        ("clean", "apply the [clean] rules to the saved Markdown"),
        ("upload", "upload the Markdown to an Open WebUI knowledge base"),
    ]:
        sub.add_parser(name, help=help_text).add_argument("config", help="site TOML file")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        site = load_config(args.config)
    except (OSError, ValueError) as e:
        parser.error(f"{args.config}: {e}")

    if args.command == "crawl":
        Crawler(site).run()
    elif args.command == "clean":
        modified, deleted = clean_dir(site.output_dir, site.clean)
        print(f"{modified} files modified, {deleted} deleted")
    elif args.command == "upload":
        api_key = os.environ.get("OPENWEBUI_API_KEY")
        if not api_key:
            parser.error("set OPENWEBUI_API_KEY in the environment")
        uploaded, failed = upload_dir(site, api_key)
        print(f"{uploaded} files uploaded, {failed} failed")
        return 1 if failed else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
