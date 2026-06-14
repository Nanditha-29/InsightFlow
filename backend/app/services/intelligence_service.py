"""Agent 3 & 4: Content Extraction Agent + Knowledge Base Agent.

Extracts intelligence from sources and stores in the knowledge base.
Covers: product intelligence, strategic intelligence, financial intelligence, hiring intelligence.
"""

import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Competitor, Source, IntelligenceSignal, TimelineEvent
from app.services.llm_service import LLMService
from app.utils.parsers import fetch_and_parse_url_sync, parse_uploaded_file


class IntelligenceService:
    """Extracts and manages intelligence signals for competitors."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def extract_from_source(self, source: Source) -> list[IntelligenceSignal]:
        """Extract intelligence signals from a single source."""
        try:
            result = fetch_and_parse_url_sync(source.url)
            content = result["content"]
            title = result["title"]
        except Exception as e:
            print(f"Failed to fetch {source.url}: {e}")
            return []

        # Use LLM to extract intelligence
        signals_data = self.llm.extract_intelligence_competitor(
            company_name=source.competitor.name if source.competitor else "",
            content=content,
            source_url=source.url,
        )

        signals = []
        for signal_data in signals_data:
            signal = IntelligenceSignal(
                competitor_id=source.competitor_id,
                source_id=source.id,
                signal_type=signal_data.get("signal_type", "general"),
                title=signal_data.get("title", "Intelligence Signal"),
                summary=signal_data.get("summary", ""),
                detail=signal_data.get("detail", None),
                confidence=signal_data.get("confidence", 0.5),
                evidence_text=signal_data.get("evidence", content[:1000]),
                source_url=source.url,
                tags=signal_data.get("tags", []),
                detected_at=datetime.now(timezone.utc),
            )
            self.db.add(signal)
            signals.append(signal)

            # Create timeline event if applicable
            if signal_data.get("is_timeline_event", False):
                event = TimelineEvent(
                    competitor_id=source.competitor_id,
                    event_type=signal_data.get("signal_type", "general"),
                    title=signal_data.get("title", ""),
                    description=signal_data.get("summary", ""),
                    event_date=datetime.now(timezone.utc),
                    source_url=source.url,
                    confidence=signal_data.get("confidence", 0.5),
                )
                self.db.add(event)

        self.db.commit()
        return signals

    def extract_from_text(self, competitor: Competitor, text: str, source_url: Optional[str] = None) -> list[IntelligenceSignal]:
        """Extract intelligence from raw text (e.g., uploaded document)."""
        signals_data = self.llm.extract_intelligence_competitor(
            company_name=competitor.name,
            content=text,
            source_url=source_url or "",
        )

        signals = []
        for signal_data in signals_data:
            signal = IntelligenceSignal(
                competitor_id=competitor.id,
                signal_type=signal_data.get("signal_type", "general"),
                title=signal_data.get("title", "Intelligence Signal"),
                summary=signal_data.get("summary", ""),
                detail=signal_data.get("detail", None),
                confidence=signal_data.get("confidence", 0.5),
                evidence_text=signal_data.get("evidence", text[:1000]),
                source_url=source_url,
                tags=signal_data.get("tags", []),
                detected_at=datetime.now(timezone.utc),
            )
            self.db.add(signal)
            signals.append(signal)

        self.db.commit()
        return signals

    def get_signals_by_type(self, competitor_id: str, signal_type: str, limit: int = 50) -> list[IntelligenceSignal]:
        """Get intelligence signals filtered by type."""
        return (
            self.db.query(IntelligenceSignal)
            .filter(
                IntelligenceSignal.competitor_id == competitor_id,
                IntelligenceSignal.signal_type == signal_type,
                IntelligenceSignal.is_active == True,
            )
            .order_by(IntelligenceSignal.detected_at.desc())
            .limit(limit)
            .all()
        )

    def get_all_signals(self, competitor_id: str, limit: int = 100) -> list[IntelligenceSignal]:
        """Get all active intelligence signals for a competitor."""
        return (
            self.db.query(IntelligenceSignal)
            .filter(
                IntelligenceSignal.competitor_id == competitor_id,
                IntelligenceSignal.is_active == True,
            )
            .order_by(IntelligenceSignal.detected_at.desc())
            .limit(limit)
            .all()
        )
