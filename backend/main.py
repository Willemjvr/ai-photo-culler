"""
FastAPI backend — AI Photo Culling & Auto-Retouching Server.
"""
from __future__ import annotations
import os
import uuid
import shutil
import tempfile
import glob
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from . import models, schemas
from .database import init_db, get_db, SessionLocal
from .pipelines import ingestion, culling, burst_grouping, retouching
from .utils import download_utils

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / ".." / "data" / "uploads"
THUMBNAIL_DIR = BASE_DIR / ".." / "data" / "thumbnails"
EXPORT_DIR = BASE_DIR / ".." / "data" / "exports"
for d in [STORAGE_DIR, THUMBNAIL_DIR, EXPORT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

os.environ["PHOTOCULLER_EXPORT_DIR"] = str(EXPORT_DIR)

# ---------------------------------------------------------------------------
# Lifespan — init DB on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Photo Culler API",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory job progress (supplemental to DB)
# ---------------------------------------------------------------------------
_job_progress: dict[str, dict] = {}


def _get_job_progress(job_id: str) -> dict:
    if job_id not in _job_progress:
        _job_progress[job_id] = {
            "processed": 0,
            "total": 0,
            "clean": 0,
            "flagged": 0,
            "status": "running",
        }
    return _job_progress[job_id]


# ---------------------------------------------------------------------------
# Routes — Ingestion & Culling
# ---------------------------------------------------------------------------
@app.post("/api/upload")
async def upload_images(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    job_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a batch of images (one folder drop)."""
    job = db.query(models.ProcessingJob).filter(
        models.ProcessingJob.job_id == job_id).first()
    if not job:
        job = models.ProcessingJob(job_id=job_id, status="running")
        db.add(job)
        db.commit()

    saved = []
    for f in files:
        safe_name = f"{uuid.uuid4().hex}_{f.filename}"
        dst = STORAGE_DIR / safe_name
        with open(dst, "wb") as buf:
            content = await f.read()
            buf.write(content)

        rec = models.ImageRecord(
            filename=f.filename or safe_name,
            original_path="",
            storage_path=str(dst),
            file_size=len(content),
            is_raw=ingestion.is_raw(f.filename or ""),
            status="pending",
        )
        db.add(rec)
        db.commit()
        saved.append(rec.id)

    job.total_images += len(saved)
    db.commit()

    _get_job_progress(job_id)["total"] += len(saved)

    # Launch async culling pipeline
    background_tasks.add_task(_run_culling_pipeline, saved, job_id)

    return {"uploaded": len(saved), "image_ids": saved, "job_id": job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.ProcessingJob).filter(
        models.ProcessingJob.job_id == job_id).first()
    if not job:
        return JSONResponse({"error": "Job not found"}, 404)
    return schemas.JobOut.model_validate(job)


@app.get("/api/images")
def list_images(
    flagged: Optional[bool] = Query(None),
    job_id: Optional[str] = Query(None),
    burst_group: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.ImageRecord)
    if flagged is not None:
        q = q.filter(models.ImageRecord.is_flagged == flagged)
    if job_id:
        job = db.query(models.ProcessingJob).filter(
            models.ProcessingJob.job_id == job_id).first()
        if job:
            # Rough: job-id match is per-session — for now return all
            pass
    if burst_group:
        q = q.filter(models.ImageRecord.burst_group_id == burst_group)
    images = q.order_by(models.ImageRecord.id).all()
    return [schemas.ImageOut.model_validate(img) for img in images]


@app.get("/api/images/{image_id}")
def get_image(image_id: int, db: Session = Depends(get_db)):
    img = db.query(models.ImageRecord).filter(
        models.ImageRecord.id == image_id).first()
    if not img:
        return JSONResponse({"error": "Not found"}, 404)
    return schemas.ImageOut.model_validate(img)


@app.get("/api/media/{image_id}")
def serve_image(image_id: int, size: str = "full", db: Session = Depends(get_db)):
    """Serve the stored image (full-res or thumbnail)."""
    img = db.query(models.ImageRecord).filter(
        models.ImageRecord.id == image_id).first()
    if not img:
        return JSONResponse({"error": "Not found"}, 404)

    path = img.thumbnail_path if size == "thumb" and img.thumbnail_path else img.storage_path
    if not path or not os.path.isfile(path):
        return JSONResponse({"error": "File not found on disk"}, 404)
    return FileResponse(path, media_type="image/jpeg",
                        filename=img.filename)


# ---------------------------------------------------------------------------
# Routes — Download
# ---------------------------------------------------------------------------
@app.get("/api/download/clean/{job_id}")
def download_clean(job_id: str, db: Session = Depends(get_db)):
    images = db.query(models.ImageRecord).filter(
        models.ImageRecord.is_flagged == False).all()
    paths = [img.storage_path for img in images if os.path.isfile(img.storage_path)]
    archive = download_utils.build_clean_zip(paths, job_id)
    if not archive or not os.path.isfile(archive):
        return JSONResponse({"error": "No clean files to download"}, 404)
    return FileResponse(archive, media_type="application/zip",
                        filename=f"clean_{job_id}.zip")


@app.get("/api/download/flagged/{job_id}")
def download_flagged(job_id: str, db: Session = Depends(get_db)):
    images = db.query(models.ImageRecord).filter(
        models.ImageRecord.is_flagged == True).all()
    paths = [img.storage_path for img in images if os.path.isfile(img.storage_path)]
    archive = download_utils.build_flagged_zip(paths, job_id)
    if not archive or not os.path.isfile(archive):
        return JSONResponse({"error": "No flagged files to download"}, 404)
    return FileResponse(archive, media_type="application/zip",
                        filename=f"flagged_{job_id}.zip")


# ---------------------------------------------------------------------------
# Routes — Retouching
# ---------------------------------------------------------------------------
@app.post("/api/retouch")
def apply_retouch(req: schemas.RetouchRequest, db: Session = Depends(get_db)):
    """Apply colour retouching to selected image IDs."""
    images = db.query(models.ImageRecord).filter(
        models.ImageRecord.id.in_(req.image_ids)).all()
    retouched_ids = []
    preview_urls = []
    for img in images:
        if not os.path.isfile(img.storage_path):
            continue
        image = ingestion.read_image(img.storage_path)
        corrected = retouching.retouch_image(image)
        out_name = f"retouched_{img.id}_{img.filename}"
        out_path = STORAGE_DIR / out_name
        cv2_success = False
        try:
            import cv2
            cv2.imwrite(str(out_path), corrected)
            cv2_success = True
        except Exception:
            from PIL import Image
            import numpy as np
            pil_img = Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
            pil_img.save(str(out_path))

        img.retouched_path = str(out_path)
        retouched_ids.append(img.id)
        preview_urls.append(f"/api/media/{img.id}?retouched=1")
        db.commit()

    return schemas.RetouchResponse(
        retouched_ids=retouched_ids,
        preview_urls=preview_urls,
    )


@app.post("/api/finetune/init")
def init_finetune(req: schemas.FineTuneInit, db: Session = Depends(get_db)):
    session = models.FineTuneSession(session_name=req.session_name)
    db.add(session)
    db.commit()
    return schemas.FineTuneStatus(
        session_id=session.id,
        session_name=session.session_name,
        num_pairs=0,
        status="pending",
    )


@app.post("/api/finetune/add-pair")
def add_finetune_pair(
    unedited: UploadFile = File(...),
    retouched: UploadFile = File(...),
    session_id: int = Form(...),
    db: Session = Depends(get_db),
):
    session = db.query(models.FineTuneSession).filter(
        models.FineTuneSession.id == session_id).first()
    if not session:
        return JSONResponse({"error": "Session not found"}, 404)

    pair_dir = STORAGE_DIR / f"finetune_{session_id}"
    pair_dir.mkdir(parents=True, exist_ok=True)

    for src, prefix in [(unedited, "inp"), (retouched, "tgt")]:
        dst = pair_dir / f"{prefix}_{uuid.uuid4().hex}_{src.filename}"
        with open(dst, "wb") as f:
            f.write(src.file.read())

    session.num_pairs += 1
    db.commit()
    return {"added": True, "total_pairs": session.num_pairs}


@app.post("/api/finetune/train/{session_id}")
def run_finetune(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.FineTuneSession).filter(
        models.FineTuneSession.id == session_id).first()
    if not session:
        return JSONResponse({"error": "Session not found"}, 404)

    pair_dir = STORAGE_DIR / f"finetune_{session_id}"
    inps = sorted(glob.glob(str(pair_dir / "inp_*")))
    tgts = sorted(glob.glob(str(pair_dir / "tgt_*")))

    if len(inps) < 5:
        return JSONResponse({"error": "Need at least 5 training pairs"}, 400)

    output_path = str(MODEL_DIR := BASE_DIR / "models" / f"custom_lut_{session_id}.pt")
    os.makedirs(BASE_DIR / "models", exist_ok=True)
    try:
        retouching.fine_tune_on_pairs(inps, tgts, output_path, epochs=10)
        session.model_path = output_path
        session.status = "completed"
        db.commit()
    except Exception as e:
        session.status = "failed"
        db.commit()
        return JSONResponse({"error": str(e)}, 500)

    return {"status": "completed", "model_path": output_path}


# ---------------------------------------------------------------------------
# Background Culling Pipeline
# ---------------------------------------------------------------------------
def _run_culling_pipeline(image_ids: list[int], job_id: str):
    """Process images: quality analysis + burst grouping + DB updates."""
    db = SessionLocal()
    progress = _get_job_progress(job_id)
    try:
        # 1. Per-image quality analysis
        for img_id in image_ids:
            rec = db.query(models.ImageRecord).filter(
                models.ImageRecord.id == img_id).first()
            if not rec or not os.path.isfile(rec.storage_path):
                continue

            rec.status = "processing"
            db.commit()

            result = culling.analyze_single_image(rec.storage_path)
            rec.is_flagged = result["is_flagged"]
            rec.flag_reasons = result["flag_reasons"]
            rec.sharpness_score = result["sharpness_score"]
            rec.global_quality_score = result["global_quality_score"]
            rec.eye_aspect_ratio = result["eye_aspect_ratio"]
            rec.exposure_flag = result["exposure_flag"]
            rec.image_width = result["image_width"]
            rec.image_height = result["image_height"]
            rec.status = "done"
            db.commit()

            progress["processed"] += 1
            if result["is_flagged"]:
                progress["flagged"] += 1
            else:
                progress["clean"] += 1

        # 2. Burst grouping via DINOv2
        done = db.query(models.ImageRecord).filter(
            models.ImageRecord.status == "done",
            models.ImageRecord.id.in_(image_ids),
        ).all()

        features = {}
        for rec in done:
            try:
                img = ingestion.read_image(rec.storage_path)
                vec = burst_grouping.compute_feature_vector(img)
                rec.feature_vector = vec
                features[rec.id] = vec
            except Exception:
                continue
        db.commit()

        if features:
            groups = burst_grouping.group_bursts(features, threshold=0.90)
            for group_leader, members in groups.items():
                group_id = f"burst_{group_leader}"
                for mid in members:
                    rec = db.query(models.ImageRecord).get(mid)
                    if rec:
                        rec.burst_group_id = group_id
                # Mark first member as best
                first = min(members)
                best = db.query(models.ImageRecord).get(first)
                if best:
                    best.is_best_in_burst = True
            db.commit()

        # 3. Finalise job
        job = db.query(models.ProcessingJob).filter(
            models.ProcessingJob.job_id == job_id).first()
        if job:
            job.status = "completed"
            job.clean_count = progress["clean"]
            job.flagged_count = progress["flagged"]
            db.commit()
        progress["status"] = "completed"

    except Exception as exc:
        progress["status"] = "failed"
        job = db.query(models.ProcessingJob).filter(
            models.ProcessingJob.job_id == job_id).first()
        if job:
            job.status = "failed"
            db.commit()
        print(f"[culling] Job {job_id} failed: {exc}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Serve static frontend (if built)
# ---------------------------------------------------------------------------
FRONTEND_DIST = BASE_DIR / ".." / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "AI Photo Culler API — build frontend with `cd frontend && npm run build`"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
