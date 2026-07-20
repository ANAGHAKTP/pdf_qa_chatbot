from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api import deps
from app.db.session import get_db
from app.db.models import User, Document, ChatSession, ChatMessage, Analytics, Role

router = APIRouter()


@router.get("/stats")
def get_platform_stats(
    current_user: User = Depends(deps.require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve platform-wide usage metrics (Admin only).
    """
    total_users = db.query(User).count()
    total_docs = db.query(Document).count()
    total_chats = db.query(ChatSession).count()
    total_messages = db.query(ChatMessage).count()
    
    # Calculate storage footprint
    storage_size_bytes = db.query(Document).with_entities(Document.file_size).all()
    total_storage_mb = sum(size[0] for size in storage_size_bytes) / 1024 / 1024
    
    # Average metrics
    avg_tokens = 0
    msgs_with_tokens = db.query(ChatMessage).filter(ChatMessage.token_count.isnot(None)).all()
    if msgs_with_tokens:
        avg_tokens = sum(m.token_count for m in msgs_with_tokens) / len(msgs_with_tokens)
        
    avg_latency = 0
    msgs_with_latency = db.query(ChatMessage).filter(ChatMessage.total_time_ms.isnot(None)).all()
    if msgs_with_latency:
        avg_latency = sum(m.total_time_ms for m in msgs_with_latency) / len(msgs_with_latency)

    return {
        "users_count": total_users,
        "documents_count": total_docs,
        "chats_count": total_chats,
        "messages_count": total_messages,
        "total_storage_mb": round(total_storage_mb, 2),
        "average_tokens_per_message": round(avg_tokens, 1),
        "average_latency_ms": round(avg_latency, 1)
    }


@router.get("/logs")
def get_analytics_logs(
    limit: int = 50,
    current_user: User = Depends(deps.require_role(Role.ADMIN)),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Retrieve platform analytics and execution logs (Admin only).
    """
    logs = db.query(Analytics).order_by(Analytics.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "endpoint": l.endpoint,
            "status_code": l.status_code,
            "response_time_ms": l.response_time_ms,
            "token_usage": l.token_usage,
            "created_at": l.created_at
        } for l in logs
    ]
