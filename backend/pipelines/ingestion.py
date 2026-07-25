"""
Image ingestion pipeline: reads standard formats + RAW camera files,
extracts metadata, generates thumbnails, and stores copies.
"""
from __future__ import annotations
import os
import cv2
import numpy as np
from PIL import Image
import rawpy
import exifread


SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp",
    ".cr2", ".nef", ".arw", ".dng", ".raf", ".rw2", ".orf",
}
RAW_EXTENSIONS = {".cr2", ".nef", ".arw", ".dng", ".raf", ".rw2", ".orf"}


def is_raw(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in RAW_EXTENSIONS


def is_supported(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in SUPPORTED_EXTENSIONS


def read_image(path: str) -> np.ndarray:
    """
    Read any supported image into a BGR numpy array (cv2 convention).
    Handles RAW files via rawpy, standard formats via cv2/PIL.
    """
    ext = os.path.splitext(path.lower())[1]
    if ext in RAW_EXTENSIONS:
        return _read_raw(path)
    # Standard format
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        # fallback via PIL
        pil_img = Image.open(path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img


def _read_raw(path: str) -> np.ndarray:
    """Read a camera raw file and return as BGR uint8."""
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=False,
            no_auto_bright=False,
            output_bps=8,
        )
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def read_exif(path: str) -> dict:
    """Extract EXIF metadata as a flat dict of tag→value strings."""
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        result = {}
        for k, v in tags.items():
            result[str(k)] = str(v)
        return result
    except Exception:
        return {}


def generate_thumbnail(
    image: np.ndarray,
    max_size: int = 300,
) -> np.ndarray:
    """Resize to fit within max_size×max_box keeping aspect ratio."""
    h, w = image.shape[:2]
    scale = max_size / max(h, w)
    if scale >= 1.0:
        return image
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
