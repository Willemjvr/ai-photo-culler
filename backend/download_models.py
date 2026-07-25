"""
Auto-download pre-trained model weights.
Call once at setup; downloads SCRFD ONNX, MediaPipe Face Landmarker,
and optional 3D-LUT checkpoint.
"""
from __future__ import annotations
import os
import sys
import urllib.request
import zipfile
import shutil

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)


SCRFD_URL = (
    "https://github.com/deepinsight/insightface/releases/download/v0.7/"
    "scrfd_10g_gnkps.onnx"
)

MEDIAPIPE_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/"
    "latest/face_landmarker_v2_with_blendshapes.task"
)


def download_file(url: str, dest: str):
    """Stream download with progress indicator."""
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        print(f"  ✓ Already exists: {os.path.basename(dest)}")
        return
    print(f"  ↓ Downloading {os.path.basename(dest)} ...")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"    Saved to {dest}")
    except Exception as e:
        print(f"    ✗ Failed: {e}")
        if os.path.isfile(dest):
            os.remove(dest)


def download_models():
    print("=" * 60)
    print("  Model Downloader — AI Photo Culler")
    print("=" * 60)

    # 1. SCRFD face detector (ONNX)
    scrfd_path = os.path.join(MODELS_DIR, "scrfd_10g_gnkps.onnx")
    print("\n[1/3] SCRFD Face Detector")
    download_file(SCRFD_URL, scrfd_path)

    # 2. MediaPipe Face Landmarker
    mp_path = os.path.join(MODELS_DIR,
                           "face_landmarker_v2_with_blendshapes.task")
    print("\n[2/3] MediaPipe Face Landmarker")
    download_file(MEDIAPIPE_URL, mp_path)

    # 3. 3D-LUT weights placeholder (optional)
    lut_path = os.path.join(MODELS_DIR, "lut3d_ppr10k.pt")
    print("\n[3/3] 3D-LUT Retouch Weights (optional)")
    if not os.path.isfile(lut_path):
        print("  ℹ  Pre-trained weights not downloaded automatically.\n"
              "     The retouching engine will use an identity/no-op LUT.\n"
              "     To download: see docs/retouch_weights.md")
    else:
        print("  ✓ Already present")

    print("\n" + "=" * 60)
    print("  Done. Models stored in:", MODELS_DIR)
    print("=" * 60)


if __name__ == "__main__":
    download_models()
