"""Vercel serverless entry point for InsightFlow FastAPI backend.
This file is deployed as a Python serverless function on Vercel.
"""

import sys
import os
from pathlib import Path

# Ensure backend is in Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

# Load .env if it exists (usually not in production, set via env vars)
env_path = backend_dir / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

# Import the FastAPI app
from app.main import app

# Vercel Python runtime expects an ASGI app
handler = app
