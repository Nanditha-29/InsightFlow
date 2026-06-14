"""Service for strategic Q&A against stored intelligence."""

from sqlalchemy.orm import Session

from app.models import Memory, Intelligence, Contradiction, QueryLog
from app.services.llm_service import LLMService


class QueryService:
    """Handles strategic questioning and answer generation."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def answer(self, workspace_id: str, query: str) -> dict:
        """Answer a strategic question using stored intelligence and memories."""
        # Get relevant context
        memories = (
            self.db.query(Memory)
            .filter(Memory.workspace_id == workspace_id, Memory.is_active == True)
            .order_by(Memory.timestamp.desc())
            .limit(20)
            .all()
        )

        intelligence = (
            self.db.query(Intelligence)
            .filter(Intelligence.workspace_id == workspace_id)
            .order_by(Intelligence.timestamp.desc())
            .limit(20)
            .all()
        )

        contradictions = (
            self.db.query(Contradiction)
            .filter(Contradiction.workspace_id == workspace_id)
            .order_by(Contradiction.timestamp.desc())
            .limit(10)
            .all()
        )

        # Combine context
        context_items = []

        # Add memories
        for m in memories:
            context_items.append({
                "type": "memory",
                "finding": m.finding,
                "assumption": m.assumption,
                "evidence": m.evidence,
                "category": m.category,
                "confidence": m.confidence,
                "source_id": m.source_id,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            })

        # Add recent intelligence
        for i in intelligence[:10]:
            context_items.append({
                "type": "intelligence",
                "company": i.company,
                "event": i.event,
                "category": i.category,
                "impact": i.impact,
                "evidence_text": i.evidence_text,
                "confidence": i.confidence,
                "timestamp": i.timestamp.isoformat() if i.timestamp else None,
            })

        # Get LLM answer
        llm_result = self.llm.answer_query(query, context_items)

        # Get source references
        sources = []
        seen_sources = set()
        for item in context_items:
            src_id = item.get("source_id") or item.get("id", "")
            if src_id and src_id not in seen_sources:
                seen_sources.add(src_id)
                sources.append({
                    "type": item.get("type", "intelligence"),
                    "finding": item.get("finding") or item.get("event", ""),
                    "category": item.get("category", ""),
                    "confidence": item.get("confidence", 0.0),
                })

        # Get relevant contradictions
        contradiction_data = []
        for c in contradictions:
            contradiction_data.append({
                "id": c.id,
                "earlier_finding": c.earlier_finding,
                "later_finding": c.later_finding,
                "type": c.contradiction_type,
                "explanation": c.explanation,
                "severity": c.severity,
            })

        # Log the query
        query_log = QueryLog(
            workspace_id=workspace_id,
            query=query,
            response=llm_result.get("answer", ""),
            sources_used=[s["finding"] for s in sources],
        )
        self.db.add(query_log)
        self.db.commit()

        return {
            "answer": llm_result.get("answer", "No answer generated."),
            "evidence": llm_result.get("evidence_used", []),
            "sources": sources[:5],
            "confidence": llm_result.get("confidence", 0.0),
            "contradictions_found": contradiction_data,
        }
