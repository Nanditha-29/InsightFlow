"""API routes for URL ingestion."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UrlIngestRequest, UrlIngestResponse
from app.models import Workspace, Intelligence
from app.services.extraction_service import ExtractionService
from app.services.memory_service import MemoryService
from app.routes.documents import get_or_create_workspace

router = APIRouter(prefix="/api/urls", tags=["urls"])


@router.post("/ingest", response_model=UrlIngestResponse)
async def ingest_url(
    request: UrlIngestRequest,
    db: Session = Depends(get_db),
):
    """Ingest content from a URL and extract intelligence."""
    url = request.url.strip()

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")

    # Get workspace
    workspace = get_or_create_workspace(db)

    # Process the URL
    extraction_service = ExtractionService(db)
    memory_service = MemoryService(db)

    try:
        doc = await extraction_service.process_url(url, workspace.id)

        # Create memories from extracted intelligence
        intelligence_list = (
            db.query(Intelligence)
            .filter(Intelligence.document_id == doc.id)
            .all()
        )
        for intel in intelligence_list:
            memory_service.create_memory_from_intelligence(intel)

        return UrlIngestResponse(
            id=doc.id,
            title=doc.title,
            url=url,
            intelligence_count=len(intelligence_list),
            message=f"Successfully ingested '{doc.title}'. Extracted {len(intelligence_list)} intelligence signals.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
