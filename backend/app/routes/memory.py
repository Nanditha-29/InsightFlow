"""API routes for memory and timeline."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MemoryResponse, TimelineResponse
from app.models import Workspace, Memory
from app.services.memory_service import MemoryService
from app.routes.documents import get_or_create_workspace

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/timeline", response_model=TimelineResponse)
def get_timeline(db: Session = Depends(get_db)):
    """Get the knowledge evolution timeline."""
    workspace = get_or_create_workspace(db)
    memory_service = MemoryService(db)
    timeline = memory_service.get_timeline(workspace.id)
    return TimelineResponse(
        timeline=timeline,
        total_entries=len(timeline),
    )


@router.get("/memories", response_model=list[MemoryResponse])
def get_memories(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get all active memories."""
    workspace = get_or_create_workspace(db)
    memories = (
        db.query(Memory)
        .filter(Memory.workspace_id == workspace.id, Memory.is_active == True)
        .order_by(Memory.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        MemoryResponse(
            id=m.id,
            finding=m.finding,
            assumption=m.assumption,
            evidence=m.evidence,
            category=m.category,
            confidence=m.confidence,
            timestamp=m.timestamp,
        )
        for m in memories
    ]
