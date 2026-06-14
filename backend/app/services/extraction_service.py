"""Service for extracting intelligence from documents and URLs."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Document, Intelligence, Workspace
from app.services.llm_service import LLMService
from app.utils.parsers import parse_uploaded_file, fetch_and_parse_url


class ExtractionService:
    """Handles intelligence extraction from various sources."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def process_uploaded_file(self, file_path: str, title: str, workspace_id: str) -> Document:
        """Process an uploaded file: extract text, extract intelligence, store."""
        # Parse the file
        content = parse_uploaded_file(file_path)

        # Create document record
        doc = Document(
            workspace_id=workspace_id,
            title=title or "Untitled Document",
            source_type="upload",
            file_path=file_path,
            content_text=content[:50000],  # Store truncated content
        )
        self.db.add(doc)
        self.db.flush()

        # Extract intelligence via LLM
        signals = self.llm.extract_intelligence(content)

        # Store each intelligence signal
        for signal in signals:
            intelligence = Intelligence(
                workspace_id=workspace_id,
                document_id=doc.id,
                company=signal.get("company", "Unknown"),
                event=signal.get("event", ""),
                category=signal.get("category", "General"),
                impact=signal.get("impact", ""),
                confidence=signal.get("confidence", 0.5),
                evidence_text=signal.get("evidence", content[:500]),
                reasoning=signal.get("reasoning", None),
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(intelligence)

        self.db.commit()
        return doc

    async def process_url(self, url: str, workspace_id: str) -> Document:
        """Process a URL: fetch, parse, extract intelligence, store."""
        # Fetch and parse the URL
        result = await fetch_and_parse_url(url)

        # Create document record
        doc = Document(
            workspace_id=workspace_id,
            title=result["title"],
            source_type="url",
            source_url=url,
            content_text=result["content"][:50000],
        )
        self.db.add(doc)
        self.db.flush()

        # Extract intelligence via LLM
        signals = self.llm.extract_intelligence(result["content"])

        # Store each intelligence signal
        for signal in signals:
            intelligence = Intelligence(
                workspace_id=workspace_id,
                document_id=doc.id,
                company=signal.get("company", "Unknown"),
                event=signal.get("event", ""),
                category=signal.get("category", "General"),
                impact=signal.get("impact", ""),
                confidence=signal.get("confidence", 0.5),
                evidence_text=signal.get("evidence", result["content"][:500]),
                reasoning=signal.get("reasoning", None),
                timestamp=datetime.now(timezone.utc),
            )
            self.db.add(intelligence)

        self.db.commit()
        return doc
