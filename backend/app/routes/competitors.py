"""API routes for competitor management — the core of InsightFlow."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Competitor, Source, IntelligenceSignal, Report, TimelineEvent, ChatSession, ChatMessage, UpdateLog
from app.services.competitor_discovery_service import CompetitorDiscoveryService
from app.services.intelligence_service import IntelligenceService
from app.services.report_service import ReportService
from app.services.chat_service import ChatService
from app.services.comparison_service import ComparisonService

router = APIRouter(prefix="/api/competitors", tags=["competitors"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CreateCompetitorRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class CompetitorResponse(BaseModel):
    id: str
    name: str
    industry: str
    description: str
    website: Optional[str] = None
    status: str
    created_at: str
    last_updated: str
    source_count: int = 0
    signal_count: int = 0
    report_count: int = 0

    class Config:
        from_attributes = True

class CompetitorListResponse(BaseModel):
    competitors: list[CompetitorResponse]
    total: int

class SourceResponse(BaseModel):
    id: str
    url: str
    title: str
    source_type: str
    category: str
    trust_score: float
    is_active: bool
    last_checked: Optional[str] = None

    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    id: str
    signal_type: str
    title: str
    summary: str
    detail: Optional[str] = None
    confidence: float
    source_url: Optional[str] = None
    tags: Optional[list] = None
    detected_at: str

    class Config:
        from_attributes = True

class TimelineEventResponse(BaseModel):
    id: str
    event_type: str
    title: str
    description: Optional[str] = None
    event_date: Optional[str] = None
    source_url: Optional[str] = None
    confidence: float
    created_at: str

    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: str
    report_type: str
    title: str
    executive_summary: Optional[str] = None
    report_data: Optional[dict] = None
    version: int
    generated_at: str

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0

class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[list] = None
    confidence: Optional[float] = None
    timestamp: str

class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

class SendMessageResponse(BaseModel):
    answer: str
    citations: list = []
    confidence: float = 0.0
    message_id: str

class CompareRequest(BaseModel):
    competitor_ids: list[str] = Field(..., min_length=1)

class RecheckResponse(BaseModel):
    status: str
    new_signals: int = 0
    changed_signals: int = 0
    removed_signals: int = 0
    total_signals: int = 0


# ---------------------------------------------------------------------------
# Helper: build competitor response
# ---------------------------------------------------------------------------
def _build_competitor_response(c: Competitor, db: Session) -> CompetitorResponse:
    source_count = db.query(Source).filter(Source.competitor_id == c.id).count()
    signal_count = db.query(IntelligenceSignal).filter(
        IntelligenceSignal.competitor_id == c.id,
        IntelligenceSignal.is_active == True,
    ).count()
    report_count = db.query(Report).filter(Report.competitor_id == c.id).count()
    return CompetitorResponse(
        id=c.id,
        name=c.name,
        industry=c.industry or "",
        description=c.description or "",
        website=c.website,
        status=c.status,
        created_at=c.created_at.isoformat() if c.created_at else "",
        last_updated=c.last_updated.isoformat() if c.last_updated else "",
        source_count=source_count,
        signal_count=signal_count,
        report_count=report_count,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=CompetitorResponse)
def create_competitor(request: CreateCompetitorRequest, db: Session = Depends(get_db)):
    """Create a competitor and auto-discover trusted sources."""
    service = CompetitorDiscoveryService(db)
    try:
        competitor = service.discover_and_create_competitor(request.name)
        return _build_competitor_response(competitor, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create competitor: {str(e)}")


@router.get("", response_model=CompetitorListResponse)
def list_competitors(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List all competitors with optional search."""
    query = db.query(Competitor).filter(Competitor.status == "active")
    if search:
        query = query.filter(Competitor.name.ilike(f"%{search}%"))
    competitors = query.order_by(Competitor.created_at.desc()).all()
    return CompetitorListResponse(
        competitors=[_build_competitor_response(c, db) for c in competitors],
        total=len(competitors),
    )


@router.get("/{competitor_id}", response_model=CompetitorResponse)
def get_competitor(competitor_id: str, db: Session = Depends(get_db)):
    """Get a competitor's details."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return _build_competitor_response(competitor, db)


@router.delete("/{competitor_id}")
def delete_competitor(competitor_id: str, db: Session = Depends(get_db)):
    """Delete (archive) a competitor."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    competitor.status = "archived"
    db.commit()
    return {"status": "archived", "id": competitor_id}


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------
@router.get("/{competitor_id}/sources", response_model=list[SourceResponse])
def get_sources(competitor_id: str, db: Session = Depends(get_db)):
    """Get all sources for a competitor."""
    sources = (
        db.query(Source)
        .filter(Source.competitor_id == competitor_id, Source.is_active == True)
        .order_by(Source.trust_score.desc())
        .all()
    )
    return [
        SourceResponse(
            id=s.id,
            url=s.url,
            title=s.title,
            source_type=s.source_type,
            category=s.category,
            trust_score=s.trust_score,
            is_active=s.is_active,
            last_checked=s.last_checked.isoformat() if s.last_checked else None,
        )
        for s in sources
    ]


# ---------------------------------------------------------------------------
# Intelligence Signals
# ---------------------------------------------------------------------------
@router.get("/{competitor_id}/signals", response_model=list[SignalResponse])
def get_signals(
    competitor_id: str,
    signal_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Get intelligence signals for a competitor, optionally filtered by type."""
    query = db.query(IntelligenceSignal).filter(
        IntelligenceSignal.competitor_id == competitor_id,
        IntelligenceSignal.is_active == True,
    )
    if signal_type:
        query = query.filter(IntelligenceSignal.signal_type == signal_type)
    signals = query.order_by(IntelligenceSignal.detected_at.desc()).limit(limit).all()
    return [
        SignalResponse(
            id=s.id,
            signal_type=s.signal_type,
            title=s.title,
            summary=s.summary,
            detail=s.detail,
            confidence=s.confidence,
            source_url=s.source_url,
            tags=s.tags,
            detected_at=s.detected_at.isoformat() if s.detected_at else "",
        )
        for s in signals
    ]


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------
@router.get("/{competitor_id}/timeline", response_model=list[TimelineEventResponse])
def get_timeline(competitor_id: str, db: Session = Depends(get_db)):
    """Get the knowledge evolution timeline for a competitor."""
    events = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.competitor_id == competitor_id)
        .order_by(TimelineEvent.event_date.desc())
        .all()
    )
    return [
        TimelineEventResponse(
            id=e.id,
            event_type=e.event_type,
            title=e.title,
            description=e.description,
            event_date=e.event_date.isoformat() if e.event_date else None,
            source_url=e.source_url,
            confidence=e.confidence,
            created_at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in events
    ]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@router.post("/{competitor_id}/reports/generate", response_model=ReportResponse)
def generate_report(competitor_id: str, db: Session = Depends(get_db)):
    """Generate a comprehensive intelligence report for a competitor."""
    report_service = ReportService(db)
    try:
        report = report_service.generate_full_report(competitor_id)
        return ReportResponse(
            id=report.id,
            report_type=report.report_type,
            title=report.title,
            executive_summary=report.executive_summary,
            report_data=report.report_data,
            version=report.version,
            generated_at=report.generated_at.isoformat() if report.generated_at else "",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/{competitor_id}/reports", response_model=list[ReportResponse])
def get_reports(competitor_id: str, db: Session = Depends(get_db)):
    """Get all reports for a competitor."""
    report_service = ReportService(db)
    reports = report_service.get_reports(competitor_id)
    return [
        ReportResponse(
            id=r.id,
            report_type=r.report_type,
            title=r.title,
            executive_summary=r.executive_summary,
            report_data=r.report_data,
            version=r.version,
            generated_at=r.generated_at.isoformat() if r.generated_at else "",
        )
        for r in reports
    ]


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
@router.post("/{competitor_id}/chat/sessions", response_model=ChatSessionResponse)
def create_chat_session(competitor_id: str, db: Session = Depends(get_db)):
    """Create a new chat session for a competitor."""
    chat_service = ChatService(db)
    session = chat_service.create_session(competitor_id)
    return ChatSessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at.isoformat() if session.created_at else "",
        updated_at=session.updated_at.isoformat() if session.updated_at else "",
        message_count=0,
    )


@router.get("/{competitor_id}/chat/sessions", response_model=list[ChatSessionResponse])
def get_chat_sessions(competitor_id: str, db: Session = Depends(get_db)):
    """Get all chat sessions for a competitor."""
    chat_service = ChatService(db)
    sessions = chat_service.get_sessions(competitor_id)
    return [
        ChatSessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at.isoformat() if s.created_at else "",
            updated_at=s.updated_at.isoformat() if s.updated_at else "",
            message_count=db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count(),
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_chat_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages in a chat session."""
    chat_service = ChatService(db)
    messages = chat_service.get_session_messages(session_id)
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations,
            confidence=m.confidence,
            timestamp=m.timestamp.isoformat() if m.timestamp else "",
        )
        for m in messages
    ]


@router.post("/chat/sessions/{session_id}/messages", response_model=SendMessageResponse)
def send_chat_message(session_id: str, request: SendMessageRequest, db: Session = Depends(get_db)):
    """Send a message and get AI response."""
    chat_service = ChatService(db)
    try:
        result = chat_service.send_message(session_id, request.content)
        return SendMessageResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            message_id=result.get("message_id", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


# ---------------------------------------------------------------------------
# Recheck Updates
# ---------------------------------------------------------------------------
@router.post("/{competitor_id}/recheck", response_model=RecheckResponse)
def recheck_updates(competitor_id: str, db: Session = Depends(get_db)):
    """Recheck all sources for new intelligence updates."""
    service = CompetitorDiscoveryService(db)
    try:
        result = service.recheck_competitor(competitor_id)
        return RecheckResponse(
            status=result["status"],
            new_signals=result["new_signals"],
            changed_signals=result["changed_signals"],
            removed_signals=result["removed_signals"],
            total_signals=result["total_signals"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recheck failed: {str(e)}")


@router.get("/{competitor_id}/updates", response_model=list)
def get_update_history(competitor_id: str, db: Session = Depends(get_db)):
    """Get update/recheck history for a competitor."""
    logs = (
        db.query(UpdateLog)
        .filter(UpdateLog.competitor_id == competitor_id)
        .order_by(UpdateLog.started_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": log.id,
            "status": log.status,
            "new_signals": log.new_signals,
            "changed_signals": log.changed_signals,
            "removed_signals": log.removed_signals,
            "summary": log.summary,
            "diff_data": log.diff_data,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }
        for log in logs
    ]


# ---------------------------------------------------------------------------
# Compare
# ---------------------------------------------------------------------------
@router.post("/compare", response_model=dict)
def compare_competitors(request: CompareRequest, db: Session = Depends(get_db)):
    """Compare multiple competitors."""
    comparison_service = ComparisonService(db)
    try:
        result = comparison_service.compare(request.competitor_ids)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


# ---------------------------------------------------------------------------
# Workspace Dashboard
# ---------------------------------------------------------------------------
@router.get("/{competitor_id}/dashboard", response_model=dict)
def get_workspace_dashboard(competitor_id: str, db: Session = Depends(get_db)):
    """Get aggregated workspace dashboard data for a competitor."""
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    source_count = db.query(Source).filter(Source.competitor_id == competitor_id, Source.is_active == True).count()
    signal_count = db.query(IntelligenceSignal).filter(
        IntelligenceSignal.competitor_id == competitor_id,
        IntelligenceSignal.is_active == True,
    ).count()
    report_count = db.query(Report).filter(Report.competitor_id == competitor_id).count()
    chat_count = db.query(ChatSession).filter(ChatSession.competitor_id == competitor_id).count()
    event_count = db.query(TimelineEvent).filter(TimelineEvent.competitor_id == competitor_id).count()

    # Signal type breakdown
    signal_types = (
        db.query(IntelligenceSignal.signal_type)
        .filter(IntelligenceSignal.competitor_id == competitor_id, IntelligenceSignal.is_active == True)
        .distinct()
        .all()
    )

    # Source type breakdown
    source_types = (
        db.query(Source.source_type, Source.trust_score)
        .filter(Source.competitor_id == competitor_id, Source.is_active == True)
        .all()
    )

    # Average trust score
    avg_trust = 0.0
    if source_types:
        avg_trust = sum(s.trust_score for s in source_types) / len(source_types)

    return {
        "competitor_name": competitor.name,
        "competitor_id": competitor.id,
        "industry": competitor.industry or "",
        "website": competitor.website,
        "last_updated": competitor.last_updated.isoformat() if competitor.last_updated else "",
        "stats": {
            "total_sources": source_count,
            "total_signals": signal_count,
            "total_reports": report_count,
            "total_chat_sessions": chat_count,
            "total_timeline_events": event_count,
            "average_trust_score": round(avg_trust, 2),
            "signal_types": [s[0] for s in signal_types if s[0]],
        },
        "recent_signals": get_recent_signals(competitor_id, db),
    }


def get_recent_signals(competitor_id: str, db: Session, limit: int = 5) -> list[dict]:
    """Helper to get recent signals for dashboard."""
    signals = (
        db.query(IntelligenceSignal)
        .filter(IntelligenceSignal.competitor_id == competitor_id, IntelligenceSignal.is_active == True)
        .order_by(IntelligenceSignal.detected_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "signal_type": s.signal_type,
            "title": s.title,
            "summary": s.summary,
            "confidence": s.confidence,
            "detected_at": s.detected_at.isoformat() if s.detected_at else "",
        }
        for s in signals
    ]
