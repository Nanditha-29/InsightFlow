"""InsightFlow - AI Competitive Intelligence & Knowledge Evolution Operating System
FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import documents, urls, memory, query, evidence
from app.routes.competitors import router as competitors_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="InsightFlow API",
    description="AI Competitive Intelligence & Knowledge Evolution Operating System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes — new competitor-centric API
app.include_router(competitors_router)

# Legacy routes (kept for backward compatibility)
app.include_router(documents.router)
app.include_router(urls.router)
app.include_router(memory.router)
app.include_router(query.router)
app.include_router(evidence.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "InsightFlow is running. Intelligence is being collected.",
    }


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "InsightFlow",
        "tagline": "AI Competitive Intelligence & Knowledge Evolution Operating System",
        "version": "1.0.0",
        "description": "Preserving not just facts, but the evolution of reasoning itself.",
        "docs": "/docs",
        "health": "/api/health",
    }
