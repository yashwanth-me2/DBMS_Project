#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Module C18 — Clinical Question-Answering System
# Start script: launches FastAPI backend (port 8000) + Streamlit frontend (port 8501)
# ─────────────────────────────────────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

echo "🏥 Starting Module 18 — Clinical QA System..."
python3 app.py
