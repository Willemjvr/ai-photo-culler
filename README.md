# 📸 AI Photo Culler

**AI-powered photo culling and auto-retouching for photographers.** Drag a folder, get clean/flagged separation, burst grouping, and one-click colour retouching — all running locally on your machine.

---

## ✨ Features

- **Folder Drag-and-Drop** — Drop an entire photo folder. Supports JPEG, PNG, TIFF, WebP, and RAW formats (CR2, NEF, ARW, DNG).
- **AI Culling Pipeline** — Each image is analysed for:
  - **Face detection** (InsightFace SCRFD ONNX)
  - **Eye-Aspect Ratio** (MediaPipe 478-landmark) → closed eyes / blink detection
  - **Face sharpness** (OpenCV Laplacian variance on face crops) → subject blur detection
  - **No-reference IQA** (PyIQA / TOPIQ) → global quality scoring
  - **Exposure analysis** (histogram tail check) → over/under exposed flags
- **Burst Grouping** — DINOv2 deep features group near-duplicate shots (cosine similarity > 0.90)
- **Independent Downloads** — Download clean photos and flagged photos as separate ZIP archives
- **AI Colour Retouching** — 3D-LUT neural colour correction (PPR10K / MIT-Adobe FiveK)
- **Custom Style Fine-Tuning** — Train the retouching model on your own before/after pairs

---

## 🏗 Architecture

```
ai-photo-culler/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # API server entry point
│   ├── database.py             # SQLite + SQLAlchemy setup
│   ├── models.py               # DB models (ImageRecord, ProcessingJob, FineTuneSession)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── download_models.py      # Auto-downloads pre-trained ML weights
│   ├── requirements.txt        # Python dependencies
│   ├── pipelines/              # Core ML pipelines
│   │   ├── ingestion.py        # File reading (RAW + standard formats)
│   │   ├── culling.py          # Quality analysis orchestrator
│   │   ├── burst_grouping.py   # DINOv2 feature extraction & clustering
│   │   └── retouching.py       # 3D-LUT colour correction engine
│   ├── utils/                  # Utility modules
│   │   ├── face_utils.py       # SCRFD + MediaPipe face/landmark pipeline
│   │   ├── quality_utils.py    # PyIQA wrapper + exposure evaluation
│   │   └── download_utils.py   # ZIP archive generator
│   └── models/                 # Downloaded model weights (auto)
├── frontend/                   # React + TypeScript + Vite + Tailwind
│   ├── src/
│   │   ├── App.tsx             # Main application with tabs & state
│   │   ├── api/client.ts       # API client (axios)
│   │   └── components/
│   │       ├── DropZone.tsx     # Drag-and-drop folder upload
│   │       ├── ImageGrid.tsx    # Image thumbnail grid with overlays
│   │       ├── TabBar.tsx       # Clean / Flagged / Retouch tabs
│   │       ├── DownloadBar.tsx  # ZIP download buttons
│   │       └── RetouchPanel.tsx # Colour retouching UI
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── setup.sh                    # Unix bootstrap
├── setup.bat                   # Windows bootstrap
├── run.py                      # Cross-platform bootstrapper + launcher
└── README.md                   # This file
```

### API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload` | Upload folder of images |
| GET | `/api/jobs/{job_id}` | Get processing job status |
| GET | `/api/images` | List images (filter: `flagged`, `burst_group`) |
| GET | `/api/images/{id}` | Get single image record |
| GET | `/api/media/{id}` | Serve image (`?size=thumb` for thumbnail) |
| GET | `/api/download/clean/{job_id}` | Download clean photos as ZIP |
| GET | `/api/download/flagged/{job_id}` | Download flagged photos as ZIP |
| POST | `/api/retouch` | Apply colour retouching |
| POST | `/api/finetune/init` | Start fine-tune session |
| POST | `/api/finetune/add-pair` | Add before/after training pair |
| POST | `/api/finetune/train/{id}` | Train custom style model |
| GET | `/api/health` | Health check |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** with `pip`
- **Node.js 18+** with `npm`
- **Git** (for version control)

### One-Command Setup

```bash
# Option A: Cross-platform Python bootstrapper
python run.py

# Option B: Shell script (Unix)
bash setup.sh

# Option C: Batch script (Windows)
setup.bat
```

### Manual Setup

```bash
# 1. Python environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

# 2. Download models
python backend/download_models.py

# 3. Frontend
cd frontend
npm install
cd ..

# 4. Start backend (terminal 1)
source .venv/bin/activate
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 5. Start frontend (terminal 2)
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🧠 ML Models

The following pre-trained models are downloaded automatically on first run:

| Model | File | Size | Source |
|-------|------|------|--------|
| SCRFD 10G Face Detector | `scrfd_10g_gnkps.onnx` | ~10 MB | InsightFace |
| MediaPipe Face Landmarker | `face_landmarker_v2_with_blendshapes.task` | ~12 MB | Google MediaPipe |
| DINOv2 (ViT-S/14) | *(TorchVision pretrained)* | ~90 MB | Meta AI |
| 3D-LUT (PPR10K) | `lut3d_ppr10k.pt` *(optional)* | ~2 MB | Download from releases |

All models are stored in `backend/models/`.

---

## ⚙️ Configuration

Thresholds in `backend/pipelines/culling.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `EAR_CLOSED_THRESHOLD` | 0.2 | EAR below this → closed eyes flag |
| `SHARPNESS_MIN` | 50.0 | Laplacian variance below this → blur flag |
| `GLOBAL_QUALITY_MIN` | 0.35 | IQA score below this → low quality flag |
| `EXPOSURE_LOW_PCT` / `EXPOSURE_HIGH_PCT` | 0.03 | Histogram tail thresholds |

Burst similarity threshold in `backend/pipelines/burst_grouping.py`: `threshold = 0.90`

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/amazing`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feat/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

- InsightFace ([DeepInsight](https://github.com/deepinsight/insightface))
- MediaPipe ([Google](https://mediapipe.dev))
- DINOv2 ([Meta AI](https://github.com/facebookresearch/dinov2))
- PyIQA ([bhowell](https://github.com/bcahill/pyiqa))
- 3D-LUT ([Zeng et al.](https://github.com/hui-zeng/Image-Adaptive-3DLUT))
