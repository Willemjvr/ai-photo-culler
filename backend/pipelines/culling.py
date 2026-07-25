"""
Core culling pipeline: per-image quality analysis.
Combines face detection, EAR, Laplacian sharpness, IQA, and exposure checks.
"""
from __future__ import annotations
import cv2
import numpy as np
from ..utils.face_utils import analyze_face
from ..utils.quality_utils import assess_global_quality, evaluate_exposure
from .ingestion import read_image


# ---------------------------------------------------------------------------
# Thresholds (tunable)
# ---------------------------------------------------------------------------
EAR_CLOSED_THRESHOLD = 0.2
SHARPNESS_MIN = 50.0          # Laplacian variance on face crop
GLOBAL_QUALITY_MIN = 0.35     # PyIQA proxy score
EXPOSURE_LOW_PCT = 0.03
EXPOSURE_HIGH_PCT = 0.03


def analyze_single_image(file_path: str) -> dict:
    """
    Full per-image evaluation.
    Returns {
        "is_flagged": bool,
        "flag_reasons": list[str],
        "sharpness_score": float | None,
        "global_quality_score": float,
        "eye_aspect_ratio": float | None,
        "exposure_flag": str,
        "has_face": bool,
        "face_bbox": list[int] | None,
        "image_width": int,
        "image_height": int,
    }
    """
    image = read_image(file_path)
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    result = {
        "is_flagged": False,
        "flag_reasons": [],
        "sharpness_score": None,
        "global_quality_score": 0.5,
        "eye_aspect_ratio": None,
        "exposure_flag": "NORMAL",
        "has_face": False,
        "face_bbox": None,
        "image_width": w,
        "image_height": h,
    }

    # 1. Face analysis (detection + EAR + Laplacian on face)
    face_info = analyze_face(image)
    result["has_face"] = face_info["has_face"]
    result["face_bbox"] = face_info["bbox"]
    result["eye_aspect_ratio"] = face_info["ear"]
    result["sharpness_score"] = face_info["sharpness_score"]

    if face_info.get("eyes_closed"):
        result["flag_reasons"].append("CLOSED_EYES")
        result["is_flagged"] = True

    if face_info["sharpness_score"] is not None and \
       face_info["sharpness_score"] < SHARPNESS_MIN:
        result["flag_reasons"].append("BLURRED_FACE")
        result["is_flagged"] = True

    # 2. Global quality assessment
    gq = assess_global_quality(image)
    result["global_quality_score"] = round(gq, 4)
    if gq < GLOBAL_QUALITY_MIN:
        result["flag_reasons"].append("LOW_QUALITY")
        result["is_flagged"] = True

    # 3. Exposure check
    exp = evaluate_exposure(gray,
                            low_pct=EXPOSURE_LOW_PCT,
                            high_pct=EXPOSURE_HIGH_PCT)
    result["exposure_flag"] = exp
    if exp != "NORMAL":
        result["flag_reasons"].append(exp)
        result["is_flagged"] = True

    return result
