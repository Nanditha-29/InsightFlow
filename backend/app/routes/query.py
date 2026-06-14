"""API routes for strategic Q&A."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.routes.documents import get_or_create_workspace

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/ask", response_model=QueryResponse)
def ask_question(
    request: QueryRequest,
    db: Session = Depends(get_db),
):
    """Ask a strategic question and get an evidence-backed answer."""
    workspace = get_or_create_workspace(db)
    query_service = QueryService(db)
    result = query_service.answer(workspace.id, request.query)
    return QueryResponse(**result)
