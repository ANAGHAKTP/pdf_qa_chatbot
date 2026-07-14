from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api import deps
from app.db.session import get_db
from app.db.models import User
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatQueryRequest, FeedbackSubmit
from app.services.chat import ChatService
from app.services.document_intelligence import DocumentIntelligenceService

router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: ChatSessionCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new conversational chat session."""
    chat_service = ChatService(db)
    return chat_service.create_session(title=session_in.title, user_id=current_user.id)


@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve all chat sessions for the authenticated user."""
    chat_service = ChatService(db)
    return chat_service.get_user_sessions(user_id=current_user.id)


@router.get("/sessions/{session_id}")
def get_session_details(
    session_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve chat history and session metadata for a specific session."""
    chat_service = ChatService(db)
    details = chat_service.get_session_history(session_id=session_id, user_id=current_user.id)
    if not details:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return details


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and its full message history."""
    chat_service = ChatService(db)
    success = chat_service.delete_session(session_id=session_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    return


@router.post("/query")
async def chat_query(
    request_in: ChatQueryRequest,
    x_nvidia_api_key: str = Header(None),  # allow client to pass api key in request headers
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit a prompt to the RAG pipeline. Streams back citations, tokens, 
    and metrics via Server-Sent Events (SSE).
    """
    # Prefer client-supplied key, fallback to env config
    api_key = x_nvidia_api_key or current_user.email  # placeholder fallback in tests
    from app.core.config import settings
    actual_api_key = x_nvidia_api_key or settings.NVIDIA_API_KEY or "nvapi-stub-key"

    chat_service = ChatService(db)
    
    # Verify user owns the document ids
    from app.repositories.document import DocumentRepository
    doc_repo = DocumentRepository(db)
    for doc_id in request_in.doc_ids:
        doc = doc_repo.get_by_id(doc_id)
        if not doc or doc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to document with ID {doc_id}"
            )

    return StreamingResponse(
        chat_service.chat_query_stream(
            session_id=request_in.session_id,
            user_id=current_user.id,
            query=request_in.query,
            doc_ids=request_in.doc_ids,
            api_key=actual_api_key
        ),
        media_type="text/event-stream"
    )


@router.post("/feedback")
def submit_feedback(
    fb_in: FeedbackSubmit,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit rating or comments for an assistant message response."""
    chat_service = ChatService(db)
    return chat_service.submit_feedback(
        message_id=fb_in.message_id,
        rating=fb_in.rating,
        comment=fb_in.comment
    )


@router.post("/documents/{id}/analyze")
def analyze_document(
    id: int,
    x_nvidia_api_key: str = Header(None),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Runs document intelligence service: extracts summary, action items, 
    risks, key insights, entities, and keywords from the PDF text.
    """
    from app.repositories.document import DocumentRepository
    doc = DocumentRepository(db).get_by_id(id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
        
    from app.core.config import settings
    api_key = x_nvidia_api_key or settings.NVIDIA_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="NVIDIA API Key required for running document intelligence analysis."
        )
        
    service = DocumentIntelligenceService(api_key=api_key)
    try:
        results = service.analyze_document(doc_id=id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
