#!/usr/bin/env bash
#
# setup.sh — AI Photo Culler: one-command bootstrap
# Usage: bash setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
echo "========================================"
echo "  AI Photo Culler — Setup"
echo "========================================"

# ── 1. Python environment ──────────────────────────────────────────
echo ""
echo "[1/4] Setting up Python environment..."

# Use uv if available, else venv + pip
if command -v uv &>/dev/null; then
  echo "  Using uv (fast)"
  if [ ! -d "$ROOT/.venv" ]; then
    uv venv "$ROOT/.venv"
  fi
  source "$ROOT/.venv/bin/activate"
  uv pip install -r "$ROOT/backend/requirements.txt"
else
  echo "  Using venv + pip"
  if [ ! -d "$ROOT/.venv" ]; then
    python3 -m venv "$ROOT/.venv"
  fi
  source "$ROOT/.venv/bin/activate"
  pip install --upgrade pip
  pip install -r "$ROOT/backend/requirements.txt"
fi

# ── 2. Download ML models ──────────────────────────────────────────
echo ""
echo "[2/4] Downloading ML model weights..."
cd "$ROOT"
python backend/download_models.py

# ── 3. Frontend ────────────────────────────────────────────────────
echo ""
echo "[3/4] Installing frontend dependencies..."
cd "$ROOT/frontend"
if command -v npm &>/dev/null; then
  npm install
else
  echo "  ⚠ npm not found. Install Node.js manually, then run: cd frontend && npm install"
fi

# ── 4. Git repo ────────────────────────────────────────────────────
echo ""
echo "[4/4] Initialising Git repository..."
cd "$ROOT"
if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "Initial commit: AI Photo Culler"
  echo "  ✓ Git repo initialised"
else
  echo "  ✓ Git repo already exists"
fi

echo ""
echo "========================================"
echo "  Setup complete!"
echo ""
echo "  Start backend:   cd $ROOT && source .venv/bin/activate && cd backend && uvicorn main:app --reload --port 8000"
echo "  Start frontend:  cd $ROOT/frontend && npm run dev"
echo "========================================"
