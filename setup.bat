@echo off
REM setup.bat — AI Photo Culler: one-command bootstrap for Windows
REM Usage: double-click or run in cmd

setlocal enabledelayedexpansion
set "ROOT=%~dp0"
echo ========================================
echo   AI Photo Culler — Setup
echo ========================================

REM ── 1. Python virtual environment ─────────────────────────────────
echo.
echo [1/4] Setting up Python environment...

where uv >nul 2>&1
if %errorlevel% equ 0 (
    echo   Using uv (fast)
    if not exist "%ROOT%.venv\" (
        uv venv "%ROOT%.venv"
    )
    call "%ROOT%.venv\Scripts\activate.bat"
    uv pip install -r "%ROOT%backend\requirements.txt"
) else (
    echo   Using venv + pip
    if not exist "%ROOT%.venv\" (
        python -m venv "%ROOT%.venv"
    )
    call "%ROOT%.venv\Scripts\activate.bat"
    python -m pip install --upgrade pip
    pip install -r "%ROOT%backend\requirements.txt"
)

REM ── 2. Download ML models ────────────────────────────────────────
echo.
echo [2/4] Downloading ML model weights...
cd /d "%ROOT%"
python backend\download_models.py

REM ── 3. Frontend ──────────────────────────────────────────────────
echo.
echo [3/4] Installing frontend dependencies...
cd /d "%ROOT%frontend"
where npm >nul 2>&1
if %errorlevel% equ 0 (
    npm install
) else (
    echo   ⚠ npm not found. Install Node.js, then run: cd frontend ^&^& npm install
)

REM ── 4. Git repo ──────────────────────────────────────────────────
echo.
echo [4/4] Initialising Git repository...
cd /d "%ROOT%"
if not exist ".git" (
    git init
    git add -A
    git commit -m "Initial commit: AI Photo Culler"
    echo   ✓ Git repo initialised
) else (
    echo   ✓ Git repo already exists
)

echo.
echo ========================================
echo   Setup complete!
echo.
echo   Start backend:  cd /d "%ROOT%" ^&^& .venv\Scripts\activate ^&^& cd backend ^&^& uvicorn main:app --reload --port 8000
echo   Start frontend: cd /d "%ROOT%frontend" ^&^& npm run dev
echo ========================================
pause
