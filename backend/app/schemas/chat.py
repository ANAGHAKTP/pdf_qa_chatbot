from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ChatSessionCreate(BaseModel):
    title: str


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatQueryRequest(BaseModel):
    session_id: str
    query: str
    doc_ids: List[int]


class FeedbackSubmit(BaseModel):
    message_id: str
    rating: int  # 1 for upvote, -1 for downvote
    comment: Optional[str] = None
