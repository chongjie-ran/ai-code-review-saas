"""
CodeLens AI - Session Storage
In-memory session storage for analysis results
"""
import uuid
from datetime import datetime
from typing import Optional
from .models.schemas import AnalyzeResponse


class SessionStore:
    """In-memory session storage"""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def store(self, response: AnalyzeResponse) -> str:
        """Store analysis result, return session_id"""
        session_id = str(uuid.uuid4())[:8]
        self._sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "response": response.model_dump(),
        }
        return session_id

    def get(self, session_id: str) -> Optional[AnalyzeResponse]:
        """Retrieve session by id"""
        data = self._sessions.get(session_id)
        if data is None:
            return None
        return AnalyzeResponse(**data["response"])

    def exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self._sessions

    def list_sessions(self, limit: int = 50) -> list[dict]:
        """List recent sessions"""
        sessions = sorted(
            self._sessions.values(),
            key=lambda x: x["created_at"],
            reverse=True,
        )
        return [
            {
                "id": s["id"],
                "created_at": s["created_at"],
                "score": s["response"]["score"],
                "summary": s["response"]["summary"],
            }
            for s in sessions[:limit]
        ]

    def delete(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global session store instance
session_store = SessionStore()
