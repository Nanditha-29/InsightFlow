"""Agent 1 & 2: Source Discovery Agent + Source Validation Agent.

Discovers trusted sources for a competitor, validates credibility, and assigns trust scores.
"""

import re
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models import Competitor, Source
from app.services.llm_service import LLMService
from app.utils.parsers import fetch_and_parse_url


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Built-in source discovery patterns
# ---------------------------------------------------------------------------
SOURCE_PATTERNS = {
    "official_website": {
        "domains": [],
        "weight": 1.0,
        "type": "official",
    },
    "blog": {
        "subdomains": ["blog", "news"],
        "paths": ["/blog", "/news", "/updates"],
        "weight": 0.9,
        "type": "official",
    },
    "linkedin": {
        "patterns": ["linkedin.com/company/"],
        "weight": 0.85,
        "type": "social",
    },
    "twitter_x": {
        "patterns": ["x.com/", "twitter.com/"],
        "weight": 0.7,
        "type": "social",
    },
    "github": {
        "patterns": ["github.com/"],
        "weight": 0.8,
        "type": "social",
    },
    "youtube": {
        "patterns": ["youtube.com/@", "youtube.com/channel/"],
        "weight": 0.75,
        "type": "social",
    },
    "medium": {
        "patterns": ["medium.com/@"],
        "weight": 0.7,
        "type": "social",
    },
}


# ---------------------------------------------------------------------------
# Trust score configuration
# ---------------------------------------------------------------------------
TRUST_SCORES = {
    "official_website": 1.0,
    "sec_filing": 1.0,
    "official_blog": 0.95,
    "press_release": 0.95,
    "reuters": 0.95,
    "bloomberg": 0.95,
    "techcrunch": 0.85,
    "forbes": 0.85,
    "business_insider": 0.80,
    "linkedin_official": 0.85,
    "github_official": 0.85,
    "youtube_official": 0.80,
    "medium_official": 0.65,
    "twitter_official": 0.70,
    "news_article": 0.75,
    "research_paper": 0.90,
    "product_docs": 0.95,
    "blog_post": 0.60,
    "unknown": 0.30,
}


class CompetitorDiscoveryService:
    """Discovers and validates trusted sources for a competitor."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def discover_and_create_competitor(self, name: str) -> Competitor:
        """Full pipeline: discover sources, validate, create competitor."""
        # Normalize name
        name = name.strip()

        # Check if already exists
        existing = self.db.query(Competitor).filter(Competitor.name == name).first()
        if existing:
            return existing

        # Step 1: Use LLM to discover sources
        discovered_sources = self._discover_sources_llm(name)

        # Step 2: Validate and assign trust scores
        validated_sources = self._validate_sources(discovered_sources)

        # Step 3: Create competitor
        competitor = Competitor(
            name=name,
            industry="",  # Will be filled during extraction
            description=f"Intelligence workspace for {name}",
            website=next(
                (s["url"] for s in validated_sources if s["source_type"] == "official_website"),
                None
            ),
        )
        self.db.add(competitor)
        self.db.flush()

        # Step 4: Create sources
        for s in validated_sources:
            source = Source(
                competitor_id=competitor.id,
                url=s["url"],
                title=s.get("title", ""),
                source_type=s["source_type"],
                category=s.get("category", "unknown"),
                trust_score=s.get("trust_score", 0.5),
                is_active=True,
                metadata_json=s.get("metadata", None),
            )
            self.db.add(source)

        self.db.commit()
        self.db.refresh(competitor)
        return competitor

    def _discover_sources_llm(self, competitor_name: str) -> list[dict]:
        """Use LLM to discover relevant sources for a competitor."""
        prompt = f"""You are a competitive intelligence source discovery agent.
Your task is to find trusted information sources for the company: {competitor_name}

Return a JSON array of source objects. For each source provide:
- url: The full URL
- title: A descriptive title for this source
- source_type: One of: official_website, official_blog, press_release, sec_filing, reuters, bloomberg, techcrunch, forbes, business_insider, linkedin_official, github_official, youtube_official, twitter_official, medium_official, news_article, research_paper, product_docs, blog_post
- category: One of: official, news, social, public

Include these categories of sources:
1. Official sources (website, blog, product pages, press releases)
2. Social media (LinkedIn, X/Twitter, GitHub, YouTube, Medium)
3. News sources (Reuters, Bloomberg, TechCrunch, Forbes, Business Insider)
4. Public sources (SEC filings, research papers, documentation)

Return ONLY a valid JSON array. No other text.
Example:
[
  {{"url": "https://www.openai.com", "title": "OpenAI Official Website", "source_type": "official_website", "category": "official"}},
  {{"url": "https://blog.openai.com", "title": "OpenAI Blog", "source_type": "official_blog", "category": "official"}}
]"""
        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            result = self.llm._extract_json(raw)
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            print(f"Source discovery error: {e}")
            # Fallback: return basic sources
            slug = competitor_name.lower().replace(" ", "").replace(".", "")
            return [
                {"url": f"https://www.{slug}.com", "title": f"{competitor_name} Official Website",
                 "source_type": "official_website", "category": "official"},
            ]

    def _validate_sources(self, sources: list[dict]) -> list[dict]:
        """Assign trust scores and filter out low-quality sources."""
        validated = []
        for source in sources:
            source_type = source.get("source_type", "unknown")
            # Assign trust score based on source type
            base_score = TRUST_SCORES.get(source_type, TRUST_SCORES["unknown"])
            source["trust_score"] = base_score

            # Only include sources with trust score >= 0.5
            if base_score >= 0.5:
                validated.append(source)

        return validated

    def recheck_competitor(self, competitor_id: str) -> dict:
        """Recheck all sources for a competitor and detect changes."""
        from app.services.intelligence_service import IntelligenceService
        from app.services.report_service import ReportService
        from app.models import UpdateLog, Source

        competitor = self.db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        # Create update log
        update_log = UpdateLog(
            competitor_id=competitor_id,
            status="running",
        )
        self.db.add(update_log)
        self.db.flush()

        try:
            # Get existing intelligence signals for diff
            from app.models import IntelligenceSignal
            old_signals = {
                s.id: s for s in self.db.query(IntelligenceSignal)
                .filter(IntelligenceSignal.competitor_id == competitor_id, IntelligenceSignal.is_active == True)
                .all()
            }

            # Run intelligence extraction on all active sources
            intel_service = IntelligenceService(self.db)
            active_sources = self.db.query(Source).filter(
                Source.competitor_id == competitor_id, Source.is_active == True
            ).all()

            new_signals = []
            for source in active_sources:
                signals = intel_service.extract_from_source(source)
                new_signals.extend(signals)

            # Detect changes (diff)
            new_signal_map = {s.id: s for s in new_signals}
            added = [s for s_id, s in new_signal_map.items() if s_id not in old_signals]
            removed = [s for s_id, s in old_signals.items() if s_id not in new_signal_map]
            changed = []
            for s_id, old_s in old_signals.items():
                if s_id in new_signal_map:
                    new_s = new_signal_map[s_id]
                    if old_s.summary != new_s.summary or old_s.confidence != new_s.confidence:
                        changed.append(new_s)

            # Generate report if there are changes
            if added or changed:
                report_service = ReportService(self.db)
                report_service.generate_update_report(competitor_id, added, changed, removed)

            # Mark old signals as inactive if removed
            for s in removed:
                s.is_active = False

            # Update last_checked for sources
            for source in active_sources:
                source.last_checked = utcnow()

            # Update update_log
            update_log.status = "completed"
            update_log.new_signals = len(added)
            update_log.changed_signals = len(changed)
            update_log.removed_signals = len(removed)
            update_log.completed_at = utcnow()
            update_log.diff_data = {
                "added": [{"title": s.title, "summary": s.summary} for s in added],
                "changed": [{"title": s.title, "summary": s.summary} for s in changed],
                "removed": [{"title": s.title, "summary": s.summary} for s in removed],
            }

            competitor.last_updated = utcnow()
            self.db.commit()

            return {
                "status": "completed",
                "new_signals": len(added),
                "changed_signals": len(changed),
                "removed_signals": len(removed),
                "total_signals": len(new_signal_map),
            }

        except Exception as e:
            update_log.status = "failed"
            self.db.commit()
            raise e
