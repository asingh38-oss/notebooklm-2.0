"""
backend/persistence.py
----------------------
Sync the local data/ folder to/from a Hugging Face Dataset repo.
This gives HF Spaces a persistent filesystem across restarts.

Uses:
    HF_TOKEN        — HF token with write access (set as Space secret)
    HF_DATASET_REPO — e.g. "asingh38/notebooklm-data" (set as Space secret)
"""

import os
import shutil
from pathlib import Path

DATA_DIR = Path("data")
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_DATASET_REPO = os.getenv("HF_DATASET_REPO", "")


def _get_api():
    from huggingface_hub import HfApi
    return HfApi(token=HF_TOKEN)


def pull_data():
    """
    Download the data/ folder from HF Dataset repo to local disk.
    Called once on app startup.
    """
    if not HF_TOKEN or not HF_DATASET_REPO:
        print("[persistence] Skipping pull — HF_TOKEN or HF_DATASET_REPO not set.")
        return

    try:
        from huggingface_hub import snapshot_download
        print(f"[persistence] Pulling data from {HF_DATASET_REPO}...")

        local_path = snapshot_download(
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            token=HF_TOKEN,
            local_dir=str(DATA_DIR),
            ignore_patterns=["*.gitattributes", ".gitattributes"],
        )
        print(f"[persistence] Pull complete → {local_path}")

    except Exception as e:
        print(f"[persistence] Pull failed (first run?): {e}")


def push_data():
    """
    Upload the local data/ folder to HF Dataset repo.
    Called after any write operation (ingest, create notebook, etc).
    """
    if not HF_TOKEN or not HF_DATASET_REPO:
        return

    if not DATA_DIR.exists():
        return

    try:
        api = _get_api()
        print(f"[persistence] Pushing data to {HF_DATASET_REPO}...")

        api.upload_folder(
            folder_path=str(DATA_DIR),
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            token=HF_TOKEN,
            commit_message="sync: notebooklm data update",
        )
        print("[persistence] Push complete.")

    except Exception as e:
        print(f"[persistence] Push failed: {e}")