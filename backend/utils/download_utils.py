"""
ZIP archive generation for batch downloads.
Creates separate .zip files for clean and flagged photo sets.
"""
from __future__ import annotations
import os
import zipfile
import tempfile
import shutil
from typing import Iterator
from . import models  # noqa: F401 — we only need schema types


def build_zip_archive(
    file_paths: list[str],
    archive_name: str = "photos.zip",
) -> str:
    """
    Creates a ZIP archive from a list of file paths.
    Returns the absolute path to the archive.
    """
    out_dir = os.environ.get("PHOTOCULLER_EXPORT_DIR",
                             tempfile.gettempdir())
    os.makedirs(out_dir, exist_ok=True)
    archive_path = os.path.join(out_dir, archive_name)

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            if os.path.isfile(fp):
                zf.write(fp, arcname=os.path.basename(fp))

    return archive_path


def build_clean_zip(clean_files: list[str],
                    job_id: str) -> str:
    return build_zip_archive(
        clean_files, archive_name=f"clean_{job_id}.zip"
    )


def build_flagged_zip(flagged_files: list[str],
                      job_id: str) -> str:
    return build_zip_archive(
        flagged_files, archive_name=f"flagged_{job_id}.zip"
    )


def cleanup_zip(archive_path: str):
    """Remove a temporary ZIP archive."""
    if os.path.isfile(archive_path):
        os.remove(archive_path)
