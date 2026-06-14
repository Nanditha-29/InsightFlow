"""Multi-Competitor Comparison Service.

Compares multiple competitors across features, market position, strategy, and SWOT.
"""

from sqlalchemy.orm import Session
from app.models import Competitor, IntelligenceSignal, Source
from app.services.llm_service import LLMService


class ComparisonService:
    """Handles multi-competitor comparisons."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def compare(self, competitor_ids: list[str]) -> dict:
        """Compare multiple competitors."""
        competitors = []
        for cid in competitor_ids:
            competitor = self.db.query(Competitor).filter(Competitor.id == cid).first()
            if not competitor:
                continue

            signals = (
                self.db.query(IntelligenceSignal)
                .filter(
                    IntelligenceSignal.competitor_id == cid,
                    IntelligenceSignal.is_active == True,
                )
                .order_by(IntelligenceSignal.detected_at.desc())
                .limit(15)
                .all()
            )

            signal_dicts = [
                {
                    "signal_type": s.signal_type,
                    "title": s.title,
                    "summary": s.summary,
                    "confidence": s.confidence,
                }
                for s in signals
            ]

            competitors.append({
                "name": competitor.name,
                "industry": competitor.industry or "",
                "signals": signal_dicts,
            })

        if not competitors:
            return {
                "executive_summary": "No competitors to compare.",
                "feature_comparison": [],
                "market_comparison": {},
                "strategy_comparison": {},
                "swot_comparison": {},
                "key_differences": [],
                "recommendations": [],
            }

        if len(competitors) == 1:
            return {
                "executive_summary": f"Single competitor analysis for {competitors[0]['name']}.",
                "feature_comparison": [],
                "market_comparison": {"market_leader": competitors[0]['name']},
                "strategy_comparison": {competitors[0]['name']: "See full report"},
                "swot_comparison": {},
                "key_differences": [],
                "recommendations": ["Add more competitors for comparison"],
            }

        # Use LLM for multi-competitor comparison
        result = self.llm.compare_competitors(competitors)
        return result
