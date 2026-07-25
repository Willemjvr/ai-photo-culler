"""SQLAlchemy models for the photo culling pipeline."""
import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
from .database import Base


class ImageRecord(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False, index=True)
    original_path = Column(String(1024), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    thumbnail_path = Column(String(1024), nullable=True)

    status = Column(String(32), default="pending")
    is_flagged = Column(Boolean, default=False)
    flag_reasons = Column(JSON, default=list)

    sharpness_score = Column(Float, nullable=True)
    global_quality_score = Column(Float, nullable=True)
    eye_aspect_ratio = Column(Float, nullable=True)
    exposure_flag = Column(String(32), nullable=True)

    burst_group_id = Column(String(64), nullable=True, index=True)
    is_best_in_burst = Column(Boolean, default=False)
    feature_vector = Column(JSON, nullable=True)

    retouched_path = Column(String(1024), nullable=True)
    retouch_params = Column(JSON, nullable=True)

    file_size = Column(Integer, nullable=True)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    camera_make = Column(String(128), nullable=True)
    camera_model = Column(String(128), nullable=True)
    is_raw = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class ProcessingJob(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(64), unique=True, nullable=False, index=True)
    folder_name = Column(String(512), nullable=True)
    total_images = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    clean_count = Column(Integer, default=0)
    flagged_count = Column(Integer, default=0)
    status = Column(String(32), default="running")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class FineTuneSession(Base):
    __tablename__ = "finetune_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_name = Column(String(256), default="My Style")
    num_pairs = Column(Integer, default=0)
    model_path = Column(String(1024), nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
