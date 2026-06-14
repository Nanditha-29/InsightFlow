"""API routes for document upload and processing."""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas import DocumentUploadResponse
from app.models import Workspace, Document, Intelligence
from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_or_create_workspace(db: Session) -> Workspace:
    """Get or create the default workspace."""
    workspace = db.query(Workspace).first()
    if not workspace:
        workspace = Workspace(name="Default Workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    return workspace


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db),
):
    """Upload a document (PDF, TXT) and extract intelligence."""
    # Validate file type
    allowed_extensions = {".pdf", ".txt", ".md"}
    ext = Path(file.filename).suffix.lower() if file.filename else ".txt"
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_extensions)}"
        )

    # Save file
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    with open(file_path, "wb") as f:
        f.write(content)

    # Get workspace
    workspace = get_or_create_workspace(db)

    # Process the file
    extraction_service = ExtractionService(db)
    memory_service = MemoryService(db)

    try:
        doc = extraction_service.process_uploaded_file(
            file_path=file_path,
            title=title or file.filename or "Untitled",
            workspace_id=workspace.id,
        )

        # Create memories from extracted intelligence
        intelligence_list = (
            db.query(Intelligence)
            .filter(Intelligence.document_id == doc.id)
            .all()
        )
        for intel in intelligence_list:
            memory_service.create_memory_from_intelligence(intel)

        return DocumentUploadResponse(
            id=doc.id,
            title=doc.title,
            source_type="upload",
            intelligence_count=len(intelligence_list),
            message=f"Successfully processed '{doc.title}'. Extracted {len(intelligence_list)} intelligence signals.",
        )
    except Exception as e:
        # Clean up the saved file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
