"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./insightflow.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-dev-key")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Groq model
    LLM_MODEL: str = "llama-3.3-70b-versatile"  # Current Groq model
    EMBEDDING_MODEL: str = "llama-3.1-8b-instant"

    # File storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(Path(__file__).parent.parent / "uploads"))
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]


settings = Settings()

# Create upload directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
