"""LLM service for interacting with Groq API — enhanced for competitor intelligence."""

import json
import re
from typing import Optional, Any
from groq import Groq
from app.config import settings


class LLMService:
    """Service for LLM interactions via Groq."""

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL

    def _extract_json(self, text: str) -> Any:
        """Extract JSON from LLM response, handling markdown code blocks."""
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            text = json_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                pass

        cleaned = re.sub(r",\s*([}\]])", r"\1", text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"Could not parse JSON from response: {text[:200]}")

    # ------------------------------------------------------------------
    # Original methods (kept for backward compatibility)
    # ------------------------------------------------------------------
    def extract_intelligence(self, text: str) -> list[dict]:
        """Extract intelligence signals from text content (original)."""
        prompt = f"""You are an AI competitive intelligence analyst. Extract key intelligence signals from the following text.

For each intelligence signal, provide:
- company: The company or entity mentioned
- event: What happened or was stated
- category: One of: Pricing, Technology, Market, Competition, Regulation, Financial, Product, Strategy, Partnership
- impact: The potential impact
- confidence: A float between 0.0 and 1.0 based on how directly stated vs inferred

Return a JSON array of objects. If no intelligence is found, return an empty array.

Text:
{text[:8000]}

Respond with ONLY a valid JSON array."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "signals" in result:
                return result["signals"]
            return []
        except Exception as e:
            print(f"LLM extraction error: {e}")
            return []

    def create_memory(self, intelligence: dict) -> dict:
        """Create a hindsight memory entry from intelligence signal."""
        prompt = f"""Convert this intelligence signal into a hindsight memory entry.

Intelligence:
Company: {intelligence.get('company', 'Unknown')}
Event: {intelligence.get('event', 'Unknown')}
Category: {intelligence.get('category', 'Unknown')}
Impact: {intelligence.get('impact', 'Unknown')}

Generate a JSON object with:
- finding: A concise statement of what we now know
- assumption: The strategic assumption this implies
- evidence: A STRING containing the evidence supporting this finding

IMPORTANT: evidence must be a plain string, not an object.

Return ONLY a valid JSON object."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            if isinstance(result.get("evidence"), dict):
                result["evidence"] = str(result["evidence"])
            return result
        except Exception as e:
            print(f"Memory creation error: {e}")
            return {
                "finding": intelligence.get("event", "Unknown finding"),
                "assumption": "Analytical assumption",
                "evidence": str(intelligence.get("impact", "No evidence available"))
            }

    def detect_contradiction(self, memory_a: dict, memory_b: dict) -> Optional[dict]:
        """Check if two memories contradict each other."""
        prompt = f"""Compare these two hindsight memories and determine if they contradict each other.

Memory A (earlier):
Finding: {memory_a.get('finding', '')}
Assumption: {memory_a.get('assumption', '')}
Category: {memory_a.get('category', '')}

Memory B (later):
Finding: {memory_b.get('finding', '')}
Assumption: {memory_b.get('assumption', '')}
Category: {memory_b.get('category', '')}

If they contradict, respond with a JSON object:
{{
    "contradiction_type": "direct" or "nuanced",
    "explanation": "Explain how these contradict",
    "severity": "high" or "medium" or "low"
}}

If they do NOT contradict, respond with: {{"contradiction": false}}

Return ONLY valid JSON, no other text."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            if result.get("contradiction") is False:
                return None
            return result
        except Exception as e:
            print(f"Contradiction detection error: {e}")
            return None

    def answer_query(self, query: str, context: list[dict]) -> dict:
        """Answer a strategic question based on stored memories and intelligence."""
        context_str = "\n\n".join([
            f"[{i+1}] Finding: {m.get('finding', m.get('event', ''))}\n"
            f"    Evidence: {m.get('evidence', m.get('evidence_text', ''))}\n"
            f"    Category: {m.get('category', '')}\n"
            f"    Confidence: {m.get('confidence', 0.0)}"
            for i, m in enumerate(context[:15])
        ])

        prompt = f"""You are InsightFlow, an AI Competitive Intelligence & Knowledge Evolution Engine.
You track how strategic understanding evolves over time.

CONTEXT (Stored Intelligence & Memories):
{context_str}

USER QUERY: {query}

Provide a response with:
1. A clear, insightful answer that references the evolution of understanding
2. Specific evidence text
3. How understanding has changed over time if applicable

Respond in this JSON format:
{{
    "answer": "Your detailed answer here...",
    "evidence_used": ["Copy the exact evidence text from context items here"],
    "confidence": 0.95
}}

IMPORTANT: evidence_used must be an array of strings containing the actual evidence text.
Return ONLY valid JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            return result
        except Exception as e:
            print(f"Query error: {e}")
            return {
                "answer": "I couldn't process this query at the moment. Please try again.",
                "evidence_used": [],
                "confidence": 0.0
            }

    # ------------------------------------------------------------------
    # New methods for competitor-centric architecture
    # ------------------------------------------------------------------
    def extract_intelligence_competitor(self, company_name: str, content: str, source_url: str) -> list[dict]:
        """Extract competitor-specific intelligence from content."""
        prompt = f"""You are an AI competitive intelligence analyst tracking: {company_name}

Extract key intelligence signals from the following content.

For each signal, return a JSON object with:
- signal_type: One of: "product" (launches, features, roadmaps), "strategic" (partnerships, acquisitions, expansion), "financial" (funding, revenue, valuation), "hiring" (hiring trends, new teams), "pricing", "regulation", "market", "general"
- title: A concise title for this intelligence
- summary: 2-3 sentence summary
- detail: Detailed description (can be null)
- confidence: Float 0.0-1.0 based on how directly stated
- evidence: Direct quote or paraphrase of the evidence
- tags: Array of relevant tags like ["pricing", "partnership", "product-launch"]
- is_timeline_event: boolean - true if this is a notable event worth tracking on a timeline

Content:
{content[:6000]}

Source URL: {source_url}

Return a JSON array of signals. If no intelligence found, return empty array [].
Return ONLY valid JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            print(f"Competitor intelligence extraction error: {e}")
            return []

    def generate_report(self, competitor_name: str, signals: list[dict], sources: list[dict]) -> dict:
        """Generate a structured intelligence report for a competitor."""
        signals_str = "\n\n".join([
            f"[{i+1}] Type: {s.get('signal_type', 'general')}\n"
            f"    Title: {s.get('title', '')}\n"
            f"    Summary: {s.get('summary', '')}\n"
            f"    Confidence: {s.get('confidence', 0.5)}\n"
            f"    Tags: {s.get('tags', [])}"
            for i, s in enumerate(signals[:30])
        ])

        sources_str = "\n".join([
            f"- {s.get('title', '')} ({s.get('source_type', '')}) | Trust: {s.get('trust_score', 0.0):.0%}"
            for s in sources[:20]
        ])

        prompt = f"""You are an AI competitive intelligence report generator.
Generate a comprehensive intelligence report for: {competitor_name}

INTELLIGENCE SIGNALS:
{signals_str}

TRUSTED SOURCES:
{sources_str}

Generate a report with the following structure as JSON:
{{
    "executive_summary": "2-3 paragraph executive summary",
    "swot": {{
        "strengths": ["strength 1", "strength 2"],
        "weaknesses": ["weakness 1", "weakness 2"],
        "opportunities": ["opportunity 1", "opportunity 2"],
        "threats": ["threat 1", "threat 2"]
    }},
    "market_position": {{
        "standing": "Description of market position",
        "key_metrics": {{"metric_name": "value"}}
    }},
    "product_analysis": {{
        "products": ["product 1", "product 2"],
        "recent_launches": ["launch 1"],
        "feature_focus": ["feature 1"]
    }},
    "strategic_insights": [
        {{"area": "Partnerships", "insight": "description"}},
        {{"area": "Expansion", "insight": "description"}}
    ],
    "risk_assessment": {{
        "overall_risk": "low/medium/high",
        "key_risks": ["risk 1", "risk 2"]
    }},
    "opportunities": ["opportunity 1", "opportunity 2"]
}}

Use the actual intelligence signals to fill the report. Be specific and evidence-based.
Return ONLY valid JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            return result
        except Exception as e:
            print(f"Report generation error: {e}")
            return {
                "executive_summary": f"Report generation failed for {competitor_name}.",
                "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
                "market_position": {"standing": "Unknown", "key_metrics": {}},
                "product_analysis": {"products": [], "recent_launches": [], "feature_focus": []},
                "strategic_insights": [],
                "risk_assessment": {"overall_risk": "unknown", "key_risks": []},
                "opportunities": [],
            }

    def chat_with_competitor(self, competitor_name: str, query: str, context_signals: list[dict], chat_history: list[dict]) -> dict:
        """Chat with a competitor's knowledge base."""
        signals_str = "\n\n".join([
            f"[{i+1}] {s.get('title', '')}\n"
            f"    {s.get('summary', '')}\n"
            f"    Source: {s.get('source_url', 'N/A')} | Confidence: {s.get('confidence', 0.5)}"
            for i, s in enumerate(context_signals[:20])
        ])

        history_str = "\n".join([
            f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')[:200]}"
            for m in chat_history[-6:]
        ]) if chat_history else "No prior conversation."

        prompt = f"""You are InsightFlow's AI Competitive Intelligence Analyst specializing in: {competitor_name}

You have access to a verified knowledge base. Only answer based on the provided intelligence signals.
If the information isn't in the knowledge base, say so.

KNOWLEDGE BASE:
{signals_str}

CONVERSATION HISTORY:
{history_str}

USER QUESTION: {query}

Respond with a JSON object:
{{
    "answer": "Your detailed answer with specific citations from the knowledge base",
    "citations": [
        {{"source": "Source title or URL", "evidence": "The specific evidence used", "confidence": 0.95}}
    ],
    "confidence": 0.9
}}

- answer must reference specific evidence from the knowledge base
- citations should include the actual source and evidence text
- confidence reflects how well the knowledge base supports this answer

Return ONLY valid JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            return result
        except Exception as e:
            print(f"Chat error: {e}")
            return {
                "answer": f"I'm having trouble retrieving information about {competitor_name}. Please try again.",
                "citations": [],
                "confidence": 0.0
            }

    def compare_competitors(self, competitors: list[dict]) -> dict:
        """Compare multiple competitors based on their intelligence data."""
        competitors_str = "\n---\n".join([
            f"COMPETITOR: {c.get('name', 'Unknown')}\n"
            f"Industry: {c.get('industry', 'N/A')}\n"
            f"Signals:\n" + "\n".join([
                f"  - [{s.get('signal_type', 'general')}] {s.get('title', '')}: {s.get('summary', '')}"
                for s in c.get('signals', [])[:10]
            ])
            for c in competitors
        ])

        prompt = f"""You are an AI competitive intelligence analyst performing a multi-competitor comparison.

COMPETITOR DATA:
{competitors_str}

Generate a comparison report as JSON:
{{
    "executive_summary": "Summary of the competitive landscape",
    "feature_comparison": [
        {{"feature": "AI Capabilities", "competitors": {{"OpenAI": "Yes", "Anthropic": "Yes", "Google": "Yes"}}}}
    ],
    "market_comparison": {{
        "market_leader": "name",
        "emerging_threats": ["name1", "name2"],
        "market_trends": ["trend 1", "trend 2"]
    }},
    "strategy_comparison": {{
        "openai": "Key strategic moves",
        "anthropic": "Key strategic moves"
    }},
    "swot_comparison": {{
        "openai": {{"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}},
        "anthropic": {{"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}}
    }},
    "key_differences": ["diff 1", "diff 2"],
    "recommendations": ["rec 1", "rec 2"]
}}

Return ONLY valid JSON."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            result = self._extract_json(raw)
            return result
        except Exception as e:
            print(f"Comparison error: {e}")
            return {
                "executive_summary": "Comparison failed.",
                "feature_comparison": [],
                "market_comparison": {},
                "strategy_comparison": {},
                "swot_comparison": {},
                "key_differences": [],
                "recommendations": [],
            }
