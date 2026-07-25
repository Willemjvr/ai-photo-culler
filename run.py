#!/usr/bin/env python3
"""
run.py — AI Photo Culler: unified bootstrapper and launcher.
Detects platform, installs dependencies, downloads models, and starts both
backend and frontend servers.

Usage:
    python run.py              # full setup + start
    python run.py --setup      # setup only (no servers)
"""
from __future__ import annotations
import argparse
import os
import platform
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND_DIR = os.path.join(ROOT, "frontend")
VENV_DIR = os.path.join(ROOT, ".venv")


def log(msg: str):
    print(f"  › {msg}")


def run(cmd, **kwargs):
    print(f"  $ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    subprocess.check_call(cmd, **kwargs)


def is_windows():
    return platform.system() == "Windows"


def venv_python():
    if is_windows():
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def setup():
    """Install all dependencies."""
    print("=" * 50)
    print("  AI Photo Culler — Setup")
    print("=" * 50)

    # 1. Python venv
    print("\n[1/4] Python environment")
    if not os.path.isdir(VENV_DIR):
        run([sys.executable, "-m", "venv", VENV_DIR])
        log(f"Created venv at {VENV_DIR}")
    else:
        log("Venv already exists")

    py = venv_python()
    if not os.path.isfile(py):
        log(f"ERROR: python not found at {py}")
        sys.exit(1)

    # Use uv if available (much faster)
    uv_path = "uv" if not is_windows() else "uv.exe"
    try:
        subprocess.run([uv_path, "--version"], capture_output=True, check=True)
        has_uv = True
    except (FileNotFoundError, subprocess.CalledProcessError):
        has_uv = False

    req = os.path.join(BACKEND_DIR, "requirements.txt")
    if has_uv:
        log("Using uv (fast)")
        run([uv_path, "pip", "install", "-r", req])
    else:
        log("Using pip")
        run([py, "-m", "pip", "install", "--upgrade", "pip"])
        run([py, "-m", "pip", "install", "-r", req])

    # 2. Download models
    print("\n[2/4] ML model weights")
    run([py, os.path.join(BACKEND_DIR, "download_models.py")])

    # 3. Frontend
    print("\n[3/4] Frontend dependencies")
    npm = "npm.cmd" if is_windows() else "npm"
    try:
        subprocess.run([npm, "--version"], capture_output=True, check=True)
        run([npm, "install"], cwd=FRONTEND_DIR)
    except (FileNotFoundError, subprocess.CalledProcessError):
        log("⚠ npm not found — install Node.js and run 'npm install' in frontend/")

    # 4. Git
    print("\n[4/4] Git repository")
    git_dir = os.path.join(ROOT, ".git")
    if not os.path.isdir(git_dir):
        run(["git", "init"], cwd=ROOT)
        run(["git", "add", "-A"], cwd=ROOT)
        run(["git", "commit", "-m", "Initial commit: AI Photo Culler"], cwd=ROOT)
        log("Git repo initialised")
    else:
        log("Git repo already exists")

    print("\n" + "=" * 50)
    print("  Setup complete!")
    print("=" * 50)


def start():
    """Launch backend and frontend servers."""
    py = venv_python()

    # Start backend
    backend_cmd = [
        py, "-m", "uvicorn", "main:app",
        "--reload", "--host", "0.0.0.0", "--port", "8000",
    ]
    log(f"Starting backend: {' '.join(backend_cmd)}")
    backend_proc = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR)

    time.sleep(2)

    # Start frontend
    npm = "npm.cmd" if is_windows() else "npm"
    frontend_cmd = [npm, "run", "dev"]
    log(f"Starting frontend: {' '.join(frontend_cmd)}")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)

    print("\n" + "=" * 50)
    print("  Servers running!")
    print(f"  Backend:  http://localhost:8000")
    print(f"  Frontend: http://localhost:5173")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        backend_proc.terminate()
        frontend_proc.terminate()
        log("Servers stopped.")


def main():
    parser = argparse.ArgumentParser(description="AI Photo Culler bootstrapper")
    parser.add_argument("--setup", action="store_true", help="Setup only (no servers)")
    args = parser.parse_args()

    setup()

    if not args.setup:
        start()


if __name__ == "__main__":
    main()
