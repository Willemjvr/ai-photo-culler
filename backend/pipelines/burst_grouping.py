"""
Burst grouping using DINOv2 deep feature vectors.
Groups near-duplicate burst shots via cosine similarity > 0.90.
"""
from __future__ import annotations
import os
import numpy as np
import torch
import cv2


_dinov2_model = None


def get_dinov2_model():
    global _dinov2_model
    if _dinov2_model is not None:
        return _dinov2_model
    try:
        import torchvision.models as tv_models
        # dinov2_vits14_reg (register-based variant works well)
        model = tv_models.dinov2_vits14(pretrained=True)
        model.eval()
        _dinov2_model = model
        return model
    except ImportError:
        raise ImportError("torchvision is required. pip install torchvision")


def _preprocess(image: np.ndarray, size: int = 224) -> torch.Tensor:
    """Resize, centre-crop, normalise → (1,3,H,W)."""
    h, w = image.shape[:2]
    # centre crop to square
    side = min(h, w)
    y0, x0 = (h - side) // 2, (w - side) // 2
    crop = image[y0:y0 + side, x0:x0 + side]
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)
    tensor = torch.from_numpy(resized).float().permute(2, 0, 1) / 255.0
    # ImageNet normalisation
    mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
    tensor = (tensor - mean) / std
    return tensor.unsqueeze(0)


def compute_feature_vector(image: np.ndarray) -> list[float]:
    """
    Returns a 384-dim (vit-small) feature vector as a plain list of floats.
    """
    model = get_dinov2_model()
    with torch.no_grad():
        inp = _preprocess(image)
        # DINOv2 returns [CLS] token at index 0
        feat = model(inp)
        vec = feat.squeeze(0).cpu().numpy().tolist()
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_np = np.array(a, dtype=np.float32)
    b_np = np.array(b, dtype=np.float32)
    denom = np.linalg.norm(a_np) * np.linalg.norm(b_np)
    if denom < 1e-8:
        return 0.0
    return float(np.dot(a_np, b_np) / denom)


def group_bursts(
    features: dict[int, list[float]],
    threshold: float = 0.90,
) -> dict[int, list[int]]:
    """
    Given a dict mapping image_id → feature_vector, return
    {group_id: [image_id, ...]} with group_id being the lowest image_id
    in each cluster.
    """
    ids = list(features.keys())
    assigned = set()
    groups: dict[int, list[int]] = {}

    for i, img_id in enumerate(ids):
        if img_id in assigned:
            continue
        group = [img_id]
        assigned.add(img_id)
        for j in range(i + 1, len(ids)):
            other_id = ids[j]
            if other_id in assigned:
                continue
            sim = cosine_similarity(features[img_id], features[other_id])
            if sim >= threshold:
                group.append(other_id)
                assigned.add(other_id)
        group.sort()
        groups[group[0]] = group

    return groups
