"""Agent 7: Competitor Chat Agent.

Handles conversational Q&A with a competitor's knowledge base.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Competitor, ChatSession, ChatMessage, IntelligenceSignal
from app.services.llm_service import LLMService


class ChatService:
    """Manages chat sessions and Q&A for competitors."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    def create_session(self, competitor_id: str, title: Optional[str] = None) -> ChatSession:
        """Create a new chat session for a competitor."""
        session = ChatSession(
            competitor_id=competitor_id,
            title=title or "New Conversation",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_sessions(self, competitor_id: str, limit: int = 20) -> list[ChatSession]:
        """Get all chat sessions for a competitor."""
        return (
            self.db.query(ChatSession)
            .filter(ChatSession.competitor_id == competitor_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .all()
        )

    def get_session_messages(self, session_id: str) -> list[ChatMessage]:
        """Get all messages in a chat session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .all()
        )

    def send_message(self, session_id: str, content: str) -> dict:
        """Send a user message and get AI response."""
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise ValueError(f"Chat session {session_id} not found")

        competitor = self.db.query(Competitor).filter(Competitor.id == session.competitor_id).first()
        if not competitor:
            raise ValueError("Competitor not found")

        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=content,
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(user_msg)
        self.db.flush()

        # Get context signals
        signals = (
            self.db.query(IntelligenceSignal)
            .filter(
                IntelligenceSignal.competitor_id == competitor.id,
                IntelligenceSignal.is_active == True,
            )
            .order_by(IntelligenceSignal.detected_at.desc())
            .limit(30)
            .all()
        )

        signal_dicts = [
            {
                "title": s.title,
                "summary": s.summary,
                "signal_type": s.signal_type,
                "confidence": s.confidence,
                "source_url": s.source_url,
            }
            for s in signals
        ]

        # Get chat history
        history = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .limit(10)
            .all()
        )

        history_dicts = [
            {"role": m.role, "content": m.content}
            for m in history[-6:]  # Last 6 messages for context
        ]

        # Get LLM response
        result = self.llm.chat_with_competitor(
            competitor_name=competitor.name,
            query=content,
            context_signals=signal_dicts,
            chat_history=history_dicts,
        )

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result.get("answer", "No response generated."),
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            timestamp=datetime.now(timezone.utc),
        )
        self.db.add(assistant_msg)

        # Update session
        session.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "answer": result.get("answer", "No response generated."),
            "citations": result.get("citations", []),
            "confidence": result.get("confidence", 0.0),
            "message_id": assistant_msg.id,
        }
