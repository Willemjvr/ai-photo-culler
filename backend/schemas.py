"""Pydantic schemas for API request/response validation."""
from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class ImageOut(BaseModel):
    id: int
    filename: str
    status: str
    is_flagged: bool
    flag_reasons: list[str]
    sharpness_score: Optional[float] = None
    global_quality_score: Optional[float] = None
    eye_aspect_ratio: Optional[float] = None
    exposure_flag: Optional[str] = None
    burst_group_id: Optional[str] = None
    is_best_in_burst: bool
    thumbnail_path: Optional[str] = None
    retouched_path: Optional[str] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    is_raw: bool

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    job_id: str
    folder_name: Optional[str] = None
    total_images: int
    processed: int
    clean_count: int
    flagged_count: int
    status: str

    class Config:
        from_attributes = True


class CullSummary(BaseModel):
    total: int
    clean: int
    flagged: int
    job_id: str
    job_status: str


class RetouchRequest(BaseModel):
    image_ids: list[int]
    style: str = "ppr10k"


class RetouchResponse(BaseModel):
    retouched_ids: list[int]
    preview_urls: list[str]


class FineTuneInit(BaseModel):
    session_name: str = "My Style"


class FineTuneStatus(BaseModel):
    session_id: int
    session_name: str
    num_pairs: int
    status: str
    model_path: Optional[str] = None
