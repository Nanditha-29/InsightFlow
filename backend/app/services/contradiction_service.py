"""Service for contradiction detection and management."""

from sqlalchemy.orm import Session

from app.models import Contradiction, Memory, Intelligence


class ContradictionService:
    """Handles detection and retrieval of contradictions."""

    def __init__(self, db: Session):
        self.db = db

    def get_contradictions(self, workspace_id: str, limit: int = 20) -> list[Contradiction]:
        """Get all contradictions for a workspace, newest first."""
        return (
            self.db.query(Contradiction)
            .filter(Contradiction.workspace_id == workspace_id)
            .order_by(Contradiction.timestamp.desc())
            .limit(limit)
            .all()
        )

    def resolve_contradiction(self, contradiction_id: str) -> bool:
        """Mark a contradiction as resolved."""
        contradiction = (
            self.db.query(Contradiction)
            .filter(Contradiction.id == contradiction_id)
            .first()
        )
        if contradiction:
            contradiction.resolved = True
            self.db.commit()
            return True
        return False
