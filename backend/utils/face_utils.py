"""
Face detection (InsightFace SCRFD ONNX) + 478-landmark prediction (MediaPipe).
Provides eye-aspect-ratio (EAR) computation for blink/closed-eye detection.
"""
from __future__ import annotations
import os
import cv2
import numpy as np
import onnxruntime as ort

# ---------------------------------------------------------------------------
# Lazy-loaded singleton for SCRFD face detector
# ---------------------------------------------------------------------------
_face_detector = None


def get_scrfd_detector(model_path: str | None = None):
    global _face_detector
    if _face_detector is not None:
        return _face_detector

    if model_path is None:
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "models", "scrfd_10g_gnkps.onnx"
        )
    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"SCRFD model not found at {model_path}. "
            "Run download_models.py first."
        )

    sess = ort.InferenceSession(
        model_path,
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    _face_detector = sess
    return sess


def detect_faces_scrfd(
    image: np.ndarray, conf_thresh: float = 0.5
) -> list[dict]:
    """
    Run SCRFD ONNX inference.
    Returns list of {bbox: [x1,y1,x2,y2], kps: [5x2], score: float}.
    """
    sess = get_scrfd_detector()
    h, w = image.shape[:2]

    # SCRFD expects 640x640 BGR input, float32, CHW
    input_size = (640, 640)
    blob = cv2.dnn.blobFromImage(
        image, 1.0 / 128.0, input_size, (127.5, 127.5, 127.5), swapRB=True
    )

    outputs = sess.run(None, {sess.get_inputs()[0].name: blob})
    # outputs[0]: (1, N, 15) -> bbox(4) + conf(1) + kps(10)
    dets = outputs[0][0]

    faces = []
    for det in dets:
        score = float(det[4])
        if score < conf_thresh:
            continue
        bbox = det[:4].tolist()  # cx, cy, bw, bh (relative)
        cx, cy, bw, bh = bbox
        x1 = float((cx - bw / 2) * w)
        y1 = float((cy - bh / 2) * h)
        x2 = float((cx + bw / 2) * w)
        y2 = float((cy + bh / 2) * h)
        # kps
        kps = det[5:15].reshape(5, 2) * np.array([[w, h]])
        faces.append({
            "bbox": [x1, y1, x2, y2],
            "kps": kps.tolist(),
            "score": score,
        })
    return faces


# ---------------------------------------------------------------------------
# MediaPipe Face Landmarker — 478 landmarks
# ---------------------------------------------------------------------------
_mp_landmarker = None


def get_mediapipe_landmarker():
    global _mp_landmarker
    if _mp_landmarker is not None:
        return _mp_landmarker

    try:
        import mediapipe as mp
        mp_face_landmarker = mp.tasks.vision.FaceLandmarker
        mp_face_landmarker_options = mp.tasks.vision.FaceLandmarkerOptions
        mp_base_options = mp.tasks.BaseOptions
    except ImportError:
        raise ImportError("mediapipe is required. pip install mediapipe")

    model_path = os.path.join(
        os.path.dirname(__file__), "..", "models",
        "face_landmarker_v2_with_blendshapes.task"
    )
    if not os.path.isfile(model_path):
        raise FileNotFoundError(
            f"MediaPipe model not found at {model_path}"
        )

    options = mp_face_landmarker_options(
        base_options=mp_base_options(model_asset_path=model_path),
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1,
    )
    _mp_landmarker = mp_face_landmarker.create_from_options(options)
    return _mp_landmarker


def compute_ear(landmarks_xy: np.ndarray) -> float:
    """
    Eye Aspect Ratio from 6 eye-landmarks per eye.
    landmarks_xy shape: (478, 2) — MediaPipe mesh.
    EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    Left eye indices: 33, 160, 158, 133, 153, 144
    Right eye indices: 362, 385, 387, 263, 373, 380
    """
    left_idx = [33, 160, 158, 133, 153, 144]
    right_idx = [362, 385, 387, 263, 373, 380]

    def _ear(idxs):
        pts = landmarks_xy[idxs]
        a = np.linalg.norm(pts[1] - pts[5])
        b = np.linalg.norm(pts[2] - pts[4])
        c = np.linalg.norm(pts[0] - pts[3])
        return float((a + b) / (2.0 * c + 1e-6))

    left_ear = _ear(left_idx)
    right_ear = _ear(right_idx)
    return (left_ear + right_ear) / 2.0


def predict_landmarks_mediapipe(
    face_crop: np.ndarray
) -> np.ndarray | None:
    """
    Returns (478, 2) array of (x,y) pixel coords or None.
    face_crop: BGR numpy array of face region.
    """
    landmarker = get_mediapipe_landmarker()
    try:
        import mediapipe as mp
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                            data=cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
        result = landmarker.detect(mp_image)
        if result.face_landmarks:
            h, w = face_crop.shape[:2]
            pts = np.array([(lm.x * w, lm.y * h)
                            for lm in result.face_landmarks[0]])
            return pts
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Convenience: full per-image face + EAR pipeline
# ---------------------------------------------------------------------------
def analyze_face(image: np.ndarray) -> dict:
    """
    Returns {
        "has_face": bool,
        "bbox": [x1,y1,x2,y2] | None,
        "sharpness_score": float | None,
        "ear": float | None,
        "eyes_closed": bool
    }
    """
    result = {
        "has_face": False,
        "bbox": None,
        "sharpness_score": None,
        "ear": None,
        "eyes_closed": None,
    }

    faces = detect_faces_scrfd(image, conf_thresh=0.3)
    if not faces:
        return result

    face = faces[0]
    x1, y1, x2, y2 = map(int, face["bbox"])
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image.shape[1], x2), min(image.shape[0], y2)

    face_crop = image[y1:y2, x1:x2]
    if face_crop.size == 0:
        return result

    result["has_face"] = True
    result["bbox"] = [x1, y1, x2, y2]

    # Landmarks → EAR
    landmarks = predict_landmarks_mediapipe(face_crop)
    if landmarks is not None:
        ear = compute_ear(landmarks)
        result["ear"] = round(ear, 4)
        result["eyes_closed"] = ear < 0.2

    # Laplacian variance on face crop
    gray_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
    lap_var = cv2.Laplacian(gray_crop, cv2.CV_64F).var()
    result["sharpness_score"] = round(float(lap_var), 2)

    return result
