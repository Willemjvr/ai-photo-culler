"""
Global image quality assessment and exposure analysis.
Combines PyIQA (no-reference IQA) with histogram-based exposure checks.
"""
from __future__ import annotations
import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Lazy-loaded PyIQA model
# ---------------------------------------------------------------------------
_iqa_model = None


def get_iqa_model():
    global _iqa_model
    if _iqa_model is not None:
        return _iqa_model
    try:
        import pyiqa
        # Use TOPIQ with default pretrained weights (no-reference)
        _iqa_model = pyiqa.create_model("topiq_nr", device="cpu")
        return _iqa_model
    except ImportError:
        raise ImportError(
            "pyiqa not installed. pip install pyiqa"
        )


def assess_global_quality(image: np.ndarray) -> float:
    """
    Returns no-reference quality score in [0, 1].
    Higher = better quality.
    """
    try:
        model = get_iqa_model()
        # pyiqa expects RGB float [0,1] or uint8, shape (H,W,C)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        score = model(rgb)
        score_val = float(score.cpu().item())
        # Normalize / clamp to [0, 1]
        return max(0.0, min(1.0, score_val))
    except Exception:
        pass

    # Fallback: BRISQUE-like proxy using sharpness + contrast
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    # Combine into a 0-1 proxy score
    raw = (np.log1p(lap_var) / 10.0 + contrast / 128.0) / 2.0
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Exposure evaluation
# ---------------------------------------------------------------------------
def evaluate_exposure(
    image: np.ndarray,
    low_pct: float = 0.02,
    high_pct: float = 0.02,
) -> str:
    """
    Returns "UNDEREXPOSED", "OVEREXPOSED", or "NORMAL".
    Analyzes luminance histogram tails.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    total = gray.size
    low_count = np.sum(gray < 16)
    high_count = np.sum(gray > 240)

    low_frac = low_count / total
    high_frac = high_count / total

    if low_frac > low_pct and high_frac > high_pct:
        return "OVEREXPOSED" if high_frac > low_frac else "UNDEREXPOSED"
    if low_frac > low_pct:
        return "UNDEREXPOSED"
    if high_frac > high_pct:
        return "OVEREXPOSED"
    return "NORMAL"
