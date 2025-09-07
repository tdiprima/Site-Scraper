#!/usr/bin/env python3
"""
Open WebUI Single-Threaded Bulk File Uploader
Optimized for servers that can't handle concurrent uploads
Increasing the time doesn't stop the "Collection failed" errors
"""

import json
import logging
import mimetypes
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import requests

# ============================================
# CONFIGURATION - MODIFY THESE VALUES
# ============================================
BASE_URL = "http://localhost:3000"
API_KEY = os.environ.get("OPENWEBUI_API_KEY")
COLLECTION_ID = "50e625ca-8b4c-4606-95ce-6ee0d4547ac2"
DIRECTORY_PATH = "stonybrook_content"  # Directory containing files to upload
FILE_LIST_PATH = (
    None  # Optional: Path to text file with file paths (set to None to use directory)
)
FILE_EXTENSIONS = (
    None  # Optional: List of extensions like ['.pdf', '.txt'] or None for all files
)
MAX_FILE_SIZE_MB = 100  # Skip files larger than this (in MB)
MIN_FILE_SIZE_BYTES = 10  # Skip files smaller than this (in bytes)

# Performance settings for single-threaded operation
DELAY_BETWEEN_UPLOADS = (
    0.5  # Seconds to wait between each upload (prevents overwhelming server)
)
DELAY_BEFORE_COLLECTION_ADD = 0.5  # Seconds to wait between upload and collection add (If that works, you could go lower (0.2-0.3 seconds))
BATCH_SIZE = 100  # Save progress every N files
RESUME_FROM_FILE = "upload_progress.json"  # File to track progress for resuming
SKIP_COLLECTION_ADD = False  # Set to True to skip adding files to collection

# ============================================
# END CONFIGURATION
# ============================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "openwebui_upload.log", mode="a"
        ),  # Append mode for resuming
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class SingleThreadedUploader:
    def __init__(self):
        """Initialize the uploader"""
        self.base_url = BASE_URL.rstrip("/")
        self.api_key = API_KEY
        self.collection_id = COLLECTION_ID
        self.max_file_size = MAX_FILE_SIZE_MB * 1024 * 1024
        self.min_file_size = MIN_FILE_SIZE_BYTES
        self.skip_collection_add = SKIP_COLLECTION_ADD
        self.delay_between_uploads = DELAY_BETWEEN_UPLOADS
        self.delay_before_collection = DELAY_BEFORE_COLLECTION_ADD

        self.headers = {"Authorization": f"Bearer {self.api_key}"}

        # Create a persistent session
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Statistics
        self.uploaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.total_size_uploaded = 0
        self.failed_files = []
        self.collection_errors = 0

        # Progress tracking
        self.progress_file = RESUME_FROM_FILE
        self.processed_files = set()
        self.load_progress()

    def load_progress(self):
        """Load previous progress if resuming"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r") as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                    self.uploaded_count = data.get("uploaded_count", 0)
                    self.failed_count = data.get("failed_count", 0)
                    self.skipped_count = data.get("skipped_count", 0)
                    self.total_size_uploaded = data.get("total_size_uploaded", 0)

                if self.processed_files:
                    logger.info(
                        f"Resuming from previous session: {len(self.processed_files)} files already processed"
                    )
            except Exception as e:
                logger.warning(f"Could not load progress file: {str(e)}")
                self.processed_files = set()

    def save_progress(self):
        """Save current progress"""
        try:
            data = {
                "processed_files": list(self.processed_files),
                "uploaded_count": self.uploaded_count,
                "failed_count": self.failed_count,
                "skipped_count": self.skipped_count,
                "total_size_uploaded": self.total_size_uploaded,
                "last_updated": datetime.now().isoformat(),
            }
            with open(self.progress_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save progress: {str(e)}")

    def verify_connection(self) -> bool:
        """Verify connection to Open WebUI"""
        try:
            # Test basic connection with longer timeout
            response = self.session.get(f"{self.base_url}/api/models", timeout=60)
            if response.status_code != 200:
                logger.error(
                    f"Failed to connect: {response.status_code} - {response.text}"
                )
                return False

            logger.info("Successfully connected to Open WebUI")

            # Test collection if we're going to use it
            if not self.skip_collection_add:
                collection_response = self.session.get(
                    f"{self.base_url}/api/v1/knowledge/{self.collection_id}", timeout=60
                )

                if collection_response.status_code == 200:
                    collection_info = collection_response.json()
                    logger.info(
                        f"Collection '{collection_info.get('name', 'Unknown')}' found"
                    )
                else:
                    logger.error(
                        f"Collection not found: {collection_response.status_code}"
                    )
                    return False
            else:
                logger.info("Skipping collection operations")

            return True

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            return False

    def upload_file(self, file_path: str) -> Tuple[bool, str]:
        """Upload a single file"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return False, f"File not found: {file_path}"

            # Get file size
            file_size = file_path_obj.stat().st_size

            # Skip small files
            if file_size < self.min_file_size:
                self.skipped_count += 1
                return False, f"File too small ({file_size} bytes)"

            # Skip large files
            if file_size > self.max_file_size:
                self.skipped_count += 1
                return False, f"File too large ({file_size / 1024 / 1024:.2f} MB)"

            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            # Calculate timeout: 60s base + 30s per MB
            base_timeout = 60
            size_based_timeout = int(file_size / (1024 * 1024) * 30)
            upload_timeout = max(base_timeout, base_timeout + size_based_timeout)
            upload_timeout = min(upload_timeout, 300)  # Cap at 5 minutes

            # Upload file
            with open(file_path, "rb") as f:
                files = {"file": (file_path_obj.name, f, mime_type)}

                response = self.session.post(
                    f"{self.base_url}/api/v1/files/",
                    files=files,
                    timeout=upload_timeout,
                )

            if response.status_code == 200:
                file_info = response.json()
                file_id = file_info.get("id")

                # Add to collection if requested
                collection_success = True
                if not self.skip_collection_add and self.collection_id and file_id:
                    # Wait before collection operation
                    time.sleep(self.delay_before_collection)

                    add_data = {"file_id": file_id}
                    add_response = self.session.post(
                        f"{self.base_url}/api/v1/knowledge/{self.collection_id}/file/add",
                        json=add_data,
                        timeout=120,  # Longer timeout for collection operations
                    )

                    if add_response.status_code != 200:
                        self.collection_errors += 1
                        collection_success = False
                        if self.collection_errors <= 3:  # Log first few errors
                            logger.warning(
                                f"Failed to add to collection: {add_response.text[:100]}"
                            )

                self.uploaded_count += 1
                self.total_size_uploaded += file_size

                status_msg = (
                    f"Uploaded: {file_path_obj.name} ({file_size / 1024:.1f} KB)"
                )
                if not self.skip_collection_add and not collection_success:
                    status_msg += " [Collection failed]"

                return True, status_msg
            else:
                error_msg = (
                    f"Upload failed ({response.status_code}): {response.text[:100]}"
                )
                return False, error_msg

        except requests.exceptions.Timeout:
            return False, f"Upload timeout (timeout: {upload_timeout}s)"
        except Exception as e:
            return False, f"Exception: {str(e)}"

    def process_files(self, file_paths: List[str]):
        """Process all files sequentially"""
        total_files = len(file_paths)
        remaining_files = [f for f in file_paths if f not in self.processed_files]

        logger.info(f"Total files: {total_files}")
        logger.info(f"Already processed: {len(self.processed_files)}")
        logger.info(f"Remaining to process: {len(remaining_files)}")

        if not remaining_files:
            logger.info("All files already processed!")
            return

        start_time = time.time()
        processed_this_session = 0

        logger.info(f"Starting single-threaded upload of {len(remaining_files)} files")
        logger.info(f"Delay between uploads: {self.delay_between_uploads} seconds")
        logger.info(
            f"Delay before collection add: {self.delay_before_collection} seconds"
        )

        for i, file_path in enumerate(remaining_files):
            try:
                # Upload file
                success, message = self.upload_file(file_path)

                if success:
                    logger.info(f"[{i+1}/{len(remaining_files)}] ✓ {message}")
                else:
                    if (
                        "too large" not in message.lower()
                        and "too small" not in message.lower()
                    ):
                        self.failed_count += 1
                        self.failed_files.append({"path": file_path, "error": message})
                        logger.error(
                            f"[{i+1}/{len(remaining_files)}] ✗ Failed: {Path(file_path).name} - {message}"
                        )
                    else:
                        logger.debug(
                            f"[{i+1}/{len(remaining_files)}] - Skipped: {Path(file_path).name} - {message}"
                        )

                # Mark as processed
                self.processed_files.add(file_path)
                processed_this_session += 1

                # Save progress periodically
                if processed_this_session % BATCH_SIZE == 0:
                    self.save_progress()
                    elapsed = time.time() - start_time
                    rate = processed_this_session / elapsed
                    remaining = len(remaining_files) - processed_this_session
                    eta = remaining / rate if rate > 0 else 0

                    logger.info(
                        f"Progress checkpoint: {processed_this_session}/{len(remaining_files)} "
                        f"({processed_this_session/len(remaining_files)*100:.1f}%) "
                        f"Rate: {rate:.1f} files/sec, ETA: {eta/3600:.1f} hours"
                    )

                # Delay between uploads to prevent overwhelming server
                if self.delay_between_uploads > 0:
                    time.sleep(self.delay_between_uploads)

            except KeyboardInterrupt:
                logger.info("Upload interrupted by user. Saving progress...")
                self.save_progress()
                sys.exit(1)
            except Exception as e:
                self.failed_count += 1
                self.failed_files.append({"path": file_path, "error": str(e)})
                logger.error(
                    f"[{i+1}/{len(remaining_files)}] Exception: {Path(file_path).name} - {str(e)}"
                )
                self.processed_files.add(file_path)  # Mark as processed to avoid retry

        # Final save
        self.save_progress()

        elapsed_time = time.time() - start_time
        self.print_summary(elapsed_time, processed_this_session)

    def print_summary(self, elapsed_time: float, processed_this_session: int):
        """Print upload summary"""
        logger.info("\n" + "=" * 60)
        logger.info("UPLOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files processed this session: {processed_this_session}")
        logger.info(f"Total files uploaded: {self.uploaded_count}")
        logger.info(f"Total failed uploads: {self.failed_count}")
        logger.info(f"Total skipped files: {self.skipped_count}")
        logger.info(f"Collection errors: {self.collection_errors}")
        logger.info(
            f"Total data uploaded: {self.total_size_uploaded / 1024 / 1024:.2f} MB"
        )
        logger.info(f"Session time: {elapsed_time/60:.2f} minutes")
        if processed_this_session > 0:
            logger.info(
                f"Session speed: {processed_this_session/elapsed_time:.2f} files/second"
            )

        if self.failed_files:
            # Save failed files list
            failed_file_path = (
                f'failed_uploads_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            with open(failed_file_path, "w") as f:
                json.dump(self.failed_files, f, indent=2)
            logger.info(f"\nFailed files saved to: {failed_file_path}")


def get_files_from_directory(
    directory: str, extensions: Optional[List[str]] = None
) -> List[str]:
    """Get all files from directory, filtering out empty files"""
    file_paths = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                if os.path.getsize(file_path) < MIN_FILE_SIZE_BYTES:
                    continue

                if extensions:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        file_paths.append(file_path)
                else:
                    file_paths.append(file_path)
            except OSError:
                continue

    return sorted(file_paths)  # Sort for consistent ordering


def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("Open WebUI Single-Threaded Bulk File Uploader")
    logger.info("=" * 60)
    logger.info(f"Configuration:")
    logger.info(f"  Base URL: {BASE_URL}")
    logger.info(f"  Collection ID: {COLLECTION_ID}")
    logger.info(f"  Max file size: {MAX_FILE_SIZE_MB} MB")
    logger.info(f"  Min file size: {MIN_FILE_SIZE_BYTES} bytes")
    logger.info(f"  Delay between uploads: {DELAY_BETWEEN_UPLOADS} seconds")
    logger.info(f"  Delay before collection add: {DELAY_BEFORE_COLLECTION_ADD} seconds")
    logger.info(f"  Batch save interval: {BATCH_SIZE} files")

    # Get file list
    if FILE_LIST_PATH:
        logger.info(f"Reading file list: {FILE_LIST_PATH}")
        try:
            with open(FILE_LIST_PATH, "r") as f:
                file_paths = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read file list: {str(e)}")
            sys.exit(1)
    else:
        logger.info(f"Scanning directory: {DIRECTORY_PATH}")
        if not os.path.exists(DIRECTORY_PATH):
            logger.error(f"Directory not found: {DIRECTORY_PATH}")
            sys.exit(1)
        file_paths = get_files_from_directory(DIRECTORY_PATH, FILE_EXTENSIONS)

    if not file_paths:
        logger.error("No files found to upload")
        sys.exit(1)

    # Initialize uploader
    uploader = SingleThreadedUploader()

    # Verify connection
    if not uploader.verify_connection():
        logger.error("Failed to connect to Open WebUI")
        sys.exit(1)

    # Process files
    try:
        uploader.process_files(file_paths)
        logger.info("✓ Upload session completed!")
    except KeyboardInterrupt:
        logger.info("Upload interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
