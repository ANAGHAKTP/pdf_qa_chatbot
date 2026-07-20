from fastapi import APIRouter
from app.api.v1.endpoints import auth, documents, chat, admin, sessions, evaluation

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
