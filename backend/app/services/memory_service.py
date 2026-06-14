"""Service for creating and managing hindsight memories."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import Intelligence, Memory, Contradiction, Workspace
from app.services.llm_service import LLMService


class MemoryService:
    """Manages the Hindsight memory system."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def create_memory_from_intelligence(self, intelligence: Intelligence) -> Memory:
        """Create a hindsight memory from an intelligence signal."""
        # Use LLM to generate a structured memory
        memory_data = self.llm.create_memory({
            "company": intelligence.company,
            "event": intelligence.event,
            "category": intelligence.category,
            "impact": intelligence.impact,
        })

        memory = Memory(
            workspace_id=intelligence.workspace_id,
            finding=memory_data.get("finding", intelligence.event),
            assumption=memory_data.get("assumption", ""),
            evidence=memory_data.get("evidence", intelligence.evidence_text),
            source_id=intelligence.document_id,
            source_type="document",
            category=intelligence.category,
            confidence=intelligence.confidence,
            is_active=True,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(memory)
        self.db.flush()

        # Detect contradictions with existing active memories
        self._detect_contradictions(memory)

        return memory

    def _detect_contradictions(self, new_memory: Memory):
        """Check new memory against existing active memories for contradictions."""
        existing_memories = (
            self.db.query(Memory)
            .filter(
                Memory.workspace_id == new_memory.workspace_id,
                Memory.id != new_memory.id,
                Memory.is_active == True,
                Memory.category == new_memory.category,
            )
            .all()
        )

        for existing in existing_memories:
            contradiction = self.llm.detect_contradiction(
                {
                    "finding": existing.finding,
                    "assumption": existing.assumption,
                    "category": existing.category,
                },
                {
                    "finding": new_memory.finding,
                    "assumption": new_memory.assumption,
                    "category": new_memory.category,
                },
            )

            if contradiction:
                # Also check which document ID corresponds to each
                existing_intel = (
                    self.db.query(Intelligence)
                    .filter(
                        Intelligence.workspace_id == existing.workspace_id,
                        Intelligence.document_id == existing.source_id,
                    )
                    .first()
                )
                new_intel = (
                    self.db.query(Intelligence)
                    .filter(
                        Intelligence.workspace_id == new_memory.workspace_id,
                        Intelligence.document_id == new_memory.source_id,
                    )
                    .first()
                )

                contradiction_record = Contradiction(
                    workspace_id=new_memory.workspace_id,
                    earlier_intelligence_id=existing_intel.id if existing_intel else None,
                    later_intelligence_id=new_intel.id if new_intel else None,
                    earlier_finding=existing.finding,
                    later_finding=new_memory.finding,
                    contradiction_type=contradiction.get("contradiction_type", "nuanced"),
                    explanation=contradiction.get("explanation", "Contradiction detected"),
                    severity=contradiction.get("severity", "medium"),
                )
                self.db.add(contradiction_record)

        self.db.commit()

    def get_timeline(self, workspace_id: str, limit: int = 50) -> list[dict]:
        """Get the knowledge evolution timeline for a workspace."""
        memories = (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id, Memory.is_active == True)
            .order_by(Memory.timestamp.asc())
            .limit(limit)
            .all()
        )

        timeline = []
        for m in memories:
            timeline.append({
                "id": m.id,
                "finding": m.finding,
                "assumption": m.assumption,
                "category": m.category,
                "confidence": m.confidence,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "month": m.timestamp.strftime("%B %Y") if m.timestamp else "Unknown",
            })

        return timeline
