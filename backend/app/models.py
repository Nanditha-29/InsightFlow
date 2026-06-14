"""SQLAlchemy models for InsightFlow — both legacy and competitor-centric models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


# ===========================================================================
# LEGACY MODELS (kept for backward compatibility with original routes)
# ===========================================================================

class Workspace(Base):
    """Isolated workspace for user data."""
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), default="Default Workspace")
    created_at = Column(DateTime, default=utcnow)

    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="workspace", cascade="all, delete-orphan")
    intelligence = relationship("Intelligence", back_populates="workspace", cascade="all, delete-orphan")
    contradictions = relationship("Contradiction", back_populates="workspace", cascade="all, delete-orphan")


class Document(Base):
    """Uploaded document or ingested URL."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(500))
    source_type = Column(String(50))  # "upload" or "url"
    source_url = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)
    doc_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    workspace = relationship("Workspace", back_populates="documents")
    intelligence = relationship("Intelligence", back_populates="document", cascade="all, delete-orphan")


class Intelligence(Base):
    """Extracted intelligence signals from documents."""
    __tablename__ = "intelligence"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    company = Column(String(255))
    event = Column(String(500))
    category = Column(String(255))
    impact = Column(String(500))
    confidence = Column(Float, default=0.0)
    evidence_text = Column(Text)
    reasoning = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    workspace = relationship("Workspace", back_populates="intelligence")
    document = relationship("Document", back_populates="intelligence")


class Memory(Base):
    """Hindsight memory - tracks evolving understanding."""
    __tablename__ = "memories"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    finding = Column(Text)
    assumption = Column(Text, nullable=True)
    evidence = Column(Text)
    source_id = Column(String(255), nullable=True)
    source_type = Column(String(50))
    category = Column(String(255))
    confidence = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    superseded_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    workspace = relationship("Workspace", back_populates="memories")


class Contradiction(Base):
    """Detected contradictions between intelligence signals."""
    __tablename__ = "contradictions"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    earlier_intelligence_id = Column(String, ForeignKey("intelligence.id"))
    later_intelligence_id = Column(String, ForeignKey("intelligence.id"))
    earlier_finding = Column(Text)
    later_finding = Column(Text)
    contradiction_type = Column(String(255))
    explanation = Column(Text)
    severity = Column(String(50))
    timestamp = Column(DateTime, default=utcnow)
    resolved = Column(Boolean, default=False)

    workspace = relationship("Workspace", back_populates="contradictions")


class QueryLog(Base):
    """Log of user queries for audit trail."""
    __tablename__ = "query_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    query = Column(Text)
    response = Column(Text, nullable=True)
    sources_used = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)


# ===========================================================================
# NEW COMPETITOR-CENTRIC MODELS
# ===========================================================================

class Competitor(Base):
    """A competitor being tracked by InsightFlow."""
    __tablename__ = "competitors"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    industry = Column(String(255), default="")
    description = Column(Text, default="")
    logo_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    last_updated = Column(DateTime, default=utcnow, onupdate=utcnow)
    status = Column(String(50), default="active")  # active, archived

    sources = relationship("Source", back_populates="competitor", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="competitor", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="competitor", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="competitor", cascade="all, delete-orphan")
    intelligence_signals = relationship("IntelligenceSignal", back_populates="competitor", cascade="all, delete-orphan")


class Source(Base):
    """A trusted or discovered source for competitor intelligence."""
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    url = Column(String(2000), nullable=False)
    title = Column(String(500), default="")
    source_type = Column(String(100))  # official_website, blog, news, social, sec_filing
    category = Column(String(100))     # official, news, social, public
    trust_score = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    last_checked = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=utcnow)
    metadata_json = Column(JSON, nullable=True)

    competitor = relationship("Competitor", back_populates="sources")


class IntelligenceSignal(Base):
    """Extracted intelligence signals about a competitor."""
    __tablename__ = "intelligence_signals"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=True)
    signal_type = Column(String(100))  # product, strategic, financial, hiring, general
    title = Column(String(500))
    summary = Column(Text)
    detail = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    evidence_text = Column(Text, nullable=True)
    source_url = Column(String(2000), nullable=True)
    tags = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=utcnow)
    is_active = Column(Boolean, default=True)

    competitor = relationship("Competitor", back_populates="intelligence_signals")
    source = relationship("Source")


class Report(Base):
    """Generated intelligence reports for a competitor."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    report_type = Column(String(100))  # full_report, swot, market_position, update
    title = Column(String(500))
    report_data = Column(JSON, nullable=True)
    executive_summary = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=utcnow)
    version = Column(Integer, default=1)

    competitor = relationship("Competitor", back_populates="reports")


class ChatSession(Base):
    """A chat session about a specific competitor."""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    title = Column(String(500), default="New Conversation")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    is_active = Column(Boolean, default=True)

    competitor = relationship("Competitor", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """A single message in a chat session."""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50))  # user, assistant
    content = Column(Text)
    citations = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utcnow)

    session = relationship("ChatSession", back_populates="messages")


class TimelineEvent(Base):
    """A tracked event in the competitor's evolution timeline."""
    __tablename__ = "timeline_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    event_type = Column(String(100))
    title = Column(String(500))
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=True)
    source_url = Column(String(2000), nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)

    competitor = relationship("Competitor", back_populates="timeline_events")


class UpdateLog(Base):
    """Logs of recheck/refresh operations."""
    __tablename__ = "update_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    competitor_id = Column(String, ForeignKey("competitors.id"), nullable=False)
    status = Column(String(50))  # running, completed, failed
    new_signals = Column(Integer, default=0)
    changed_signals = Column(Integer, default=0)
    removed_signals = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    diff_data = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)

    competitor = relationship("Competitor")
