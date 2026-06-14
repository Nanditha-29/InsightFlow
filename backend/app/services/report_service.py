"""Agent 6: Report Generation Agent.

Generates structured intelligence reports including SWOT, market position, and update reports.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Competitor, Source, IntelligenceSignal, Report, TimelineEvent
from app.services.llm_service import LLMService


class ReportService:
    """Generates intelligence reports for competitors."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def generate_full_report(self, competitor_id: str) -> Report:
        """Generate a comprehensive intelligence report for a competitor."""
        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        signals = (
            self.db.query(IntelligenceSignal)
            .filter(
                IntelligenceSignal.competitor_id == competitor_id,
                IntelligenceSignal.is_active == True,
            )
            .order_by(IntelligenceSignal.detected_at.desc())
            .all()
        )

        sources = (
            self.db.query(Source)
            .filter(Source.competitor_id == competitor_id, Source.is_active == True)
            .all()
        )

        # Count versions
        existing_reports = self.db.query(Report).filter(Report.competitor_id == competitor_id).count()

        # Build signal dicts
        signal_dicts = [
            {
                "signal_type": s.signal_type,
                "title": s.title,
                "summary": s.summary,
                "detail": s.detail,
                "confidence": s.confidence,
                "tags": s.tags or [],
                "source_url": s.source_url,
            }
            for s in signals
        ]

        source_dicts = [
            {
                "title": s.title,
                "url": s.url,
                "source_type": s.source_type,
                "trust_score": s.trust_score,
            }
            for s in sources
        ]

        # Use LLM to generate report
        report_data = self.llm.generate_report(competitor.name, signal_dicts, source_dicts)

        # Create report record
        report = Report(
            competitor_id=competitor_id,
            report_type="full_report",
            title=f"Intelligence Report: {competitor.name} - Version {existing_reports + 1}",
            report_data=report_data,
            executive_summary=report_data.get("executive_summary", ""),
            generated_at=datetime.now(timezone.utc),
            version=existing_reports + 1,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def generate_swot_report(self, competitor_id: str) -> Report:
        """Generate a focused SWOT analysis report."""
        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        signals = (
            self.db.query(IntelligenceSignal)
            .filter(
                IntelligenceSignal.competitor_id == competitor_id,
                IntelligenceSignal.is_active == True,
            )
            .all()
        )

        # First get the full report and extract SWOT
        signal_dicts = [
            {
                "signal_type": s.signal_type,
                "title": s.title,
                "summary": s.summary,
                "confidence": s.confidence,
            }
            for s in signals
        ]

        sources = self.db.query(Source).filter(Source.competitor_id == competitor_id).all()
        source_dicts = [
            {"title": s.title, "source_type": s.source_type, "trust_score": s.trust_score}
            for s in sources
        ]

        full_report = self.llm.generate_report(competitor.name, signal_dicts, source_dicts)
        swot_data = full_report.get("swot", {})

        report = Report(
            competitor_id=competitor_id,
            report_type="swot",
            title=f"SWOT Analysis: {competitor.name}",
            report_data={"swot": swot_data},
            executive_summary=f"SWOT analysis for {competitor.name}",
            generated_at=datetime.now(timezone.utc),
            version=1,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def generate_update_report(self, competitor_id: str, added: list, changed: list, removed: list) -> Report:
        """Generate a what's-new update report after recheck."""
        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        existing_reports = self.db.query(Report).filter(Report.competitor_id == competitor_id).count()

        update_data = {
            "update_type": "intelligence_refresh",
            "new_signals": [
                {"title": s.title, "summary": s.summary, "signal_type": s.signal_type}
                for s in added
            ],
            "changed_signals": [
                {"title": s.title, "summary": s.summary, "signal_type": s.signal_type}
                for s in changed
            ],
            "removed_signals": [
                {"title": s.title, "summary": s.summary, "signal_type": s.signal_type}
                for s in removed
            ],
        }

        report = Report(
            competitor_id=competitor_id,
            report_type="update",
            title=f"Intelligence Update: {competitor.name} - What's New",
            report_data=update_data,
            executive_summary=(
                f"Found {len(added)} new signals, "
                f"{len(changed)} changed, "
                f"{len(removed)} removed for {competitor.name}."
            ),
            generated_at=datetime.now(timezone.utc),
            version=existing_reports + 1,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports(self, competitor_id: str, limit: int = 10) -> list[Report]:
        """Get all reports for a competitor."""
        return (
            self.db.query(Report)
            .filter(Report.competitor_id == competitor_id)
            .order_by(Report.generated_at.desc())
            .limit(limit)
            .all()
        )

    def get_report_by_id(self, report_id: str) -> Report:
        """Get a specific report by ID."""
        return self.db.query(Report).filter(Report.id == report_id).first()
