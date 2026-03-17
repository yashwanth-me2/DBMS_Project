"""
Module C18 — Clinical Question-Answering System
Entry-point file.  Usage:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
Or use start.sh / run.py to launch both backend + frontend together.
"""

from backend.backend import app  # noqa: F401 — re-export the FastAPI instance
