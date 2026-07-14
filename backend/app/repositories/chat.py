from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import ChatSession, ChatMessage, Feedback


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    # Session methods
    def create_session(self, title: str, user_id: int) -> ChatSession:
        session = ChatSession(title=title, user_id=user_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str, user_id: int) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()

    def get_user_sessions(self, user_id: int, limit: int = 50) -> List[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).limit(limit).all()

    def delete_session(self, session_id: str, user_id: int) -> bool:
        session = self.get_session(session_id, user_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False

    def update_session_title(self, session_id: str, user_id: int, new_title: str) -> Optional[ChatSession]:
        session = self.get_session(session_id, user_id)
        if session:
            session.title = new_title
            self.db.commit()
            self.db.refresh(session)
            return session
        return None

    # Message methods
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: Optional[List[dict]] = None,
        embedding_time_ms: Optional[float] = None,
        retrieval_time_ms: Optional[float] = None,
        llm_time_ms: Optional[float] = None,
        total_time_ms: Optional[float] = None,
        token_count: Optional[int] = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            embedding_time_ms=embedding_time_ms,
            retrieval_time_ms=retrieval_time_ms,
            llm_time_ms=llm_time_ms,
            total_time_ms=total_time_ms,
            token_count=token_count
        )
        self.db.add(message)
        
        # Touch the parent session's updated_at timestamp
        session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            import datetime
            session.updated_at = datetime.datetime.utcnow()
            
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()

    # Feedback methods
    def submit_feedback(self, message_id: str, rating: int, comment: Optional[str] = None) -> Feedback:
        # Check if feedback already exists for this message
        existing = self.db.query(Feedback).filter(Feedback.message_id == message_id).first()
        if existing:
            existing.rating = rating
            existing.comment = comment
            self.db.commit()
            self.db.refresh(existing)
            return existing
            
        fb = Feedback(message_id=message_id, rating=rating, comment=comment)
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb
