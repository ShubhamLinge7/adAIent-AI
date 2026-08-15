"""
Session management for chat-based troubleshooting.
Stores context and history for follow-up questions.
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChatSession:
    """Represents a chat session with context."""
    session_id: str
    manual_id: str
    question: str
    answer: str
    context_chunks: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


class SessionStore:
    """In-memory store for chat sessions."""
    
    def __init__(self):
        """Initialize session store."""
        self.sessions: Dict[str, ChatSession] = {}
        logger.info("Session store initialized")
    
    def create_session(
        self,
        manual_id: str,
        question: str,
        answer: str,
        context_chunks: List[str],
        steps: Optional[List[str]] = None
    ) -> str:
        """
        Create a new chat session.
        
        Args:
            manual_id: ID of the manual
            question: Initial question
            answer: Initial answer
            context_chunks: Retrieved context
            steps: Parsed steps from answer
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        session = ChatSession(
            session_id=session_id,
            manual_id=manual_id,
            question=question,
            answer=answer,
            context_chunks=context_chunks,
            steps=steps or []
        )
        
        self.sessions[session_id] = session
        logger.info(f"Created session: {session_id} for manual: {manual_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def update_session(
        self,
        session_id: str,
        question: str,
        answer: str
    ) -> None:
        """Update session with new Q&A."""
        session = self.sessions.get(session_id)
        if session:
            session.question = question
            session.answer = answer
            session.last_updated = datetime.now()
            logger.info(f"Updated session: {session_id}")
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """Remove sessions older than max_age_hours."""
        now = datetime.now()
        to_delete = []
        
        for sid, session in self.sessions.items():
            age_hours = (now - session.last_updated).total_seconds() / 3600
            if age_hours > max_age_hours:
                to_delete.append(sid)
        
        for sid in to_delete:
            self.delete_session(sid)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")


# Global session store instance
_session_store = None


def get_session_store() -> SessionStore:
    """Get or create the global session store instance."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
