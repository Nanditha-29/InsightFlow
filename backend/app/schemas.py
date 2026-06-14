"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: str
    title: str
    source_type: str
    intelligence_count: int
    message: str


class IntelligenceResponse(BaseModel):
    id: str
    company: str
    event: str
    category: str
    impact: str
    confidence: float
    evidence_text: str
    reasoning: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class MemoryResponse(BaseModel):
    id: str
    finding: str
    assumption: Optional[str] = None
    evidence: str
    category: str
    confidence: float
    timestamp: datetime

    class Config:
        from_attributes = True


class ContradictionResponse(BaseModel):
    id: str
    earlier_finding: str
    later_finding: str
    contradiction_type: str
    explanation: str
    severity: str
    timestamp: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    answer: str = ""
    evidence: list = []
    sources: list[dict] = []
    confidence: float = 0.0
    contradictions_found: list[dict] = []


class TimelineResponse(BaseModel):
    timeline: list[dict]
    total_entries: int


class UrlIngestRequest(BaseModel):
    url: str = Field(..., min_length=1)


class UrlIngestResponse(BaseModel):
    id: str
    title: str
    url: str
    intelligence_count: int
    message: str


class EvidenceExplorerResponse(BaseModel):
    total_memories: int
    total_intelligence: int
    total_contradictions: int
    categories: list[str]
    recent_memories: list[MemoryResponse]
