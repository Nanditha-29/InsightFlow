"""API routes for evidence explorer."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EvidenceExplorerResponse, MemoryResponse
from app.models import Workspace, Memory, Intelligence, Contradiction
from app.services.contradiction_service import ContradictionService
from app.routes.documents import get_or_create_workspace

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.get("/explorer", response_model=EvidenceExplorerResponse)
def evidence_explorer(db: Session = Depends(get_db)):
    """Get a comprehensive view of all evidence, memories, and contradictions."""
    workspace = get_or_create_workspace(db)

    total_memories = (
        db.query(Memory)
        .filter(Memory.workspace_id == workspace.id, Memory.is_active == True)
        .count()
    )

    total_intelligence = (
        db.query(Intelligence)
        .filter(Intelligence.workspace_id == workspace.id)
        .count()
    )

    total_contradictions = (
        db.query(Contradiction)
        .filter(Contradiction.workspace_id == workspace.id)
        .count()
    )

    # Get unique categories
    categories_result = (
        db.query(Memory.category)
        .filter(Memory.workspace_id == workspace.id, Memory.is_active == True)
        .distinct()
        .all()
    )
    categories = [c[0] for c in categories_result if c[0]]

    # Get recent memories
    recent_memories = (
        db.query(Memory)
        .filter(Memory.workspace_id == workspace.id, Memory.is_active == True)
        .order_by(Memory.timestamp.desc())
        .limit(15)
        .all()
    )

    return EvidenceExplorerResponse(
        total_memories=total_memories,
        total_intelligence=total_intelligence,
        total_contradictions=total_contradictions,
        categories=categories,
        recent_memories=[
            MemoryResponse(
                id=m.id,
                finding=m.finding,
                assumption=m.assumption,
                evidence=m.evidence,
                category=m.category,
                confidence=m.confidence,
                timestamp=m.timestamp,
            )
            for m in recent_memories
        ],
    )
