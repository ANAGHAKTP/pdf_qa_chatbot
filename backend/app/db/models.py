import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Float
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    analytics = relationship("Analytics", back_populates="user")


class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="folders")
    documents = relationship("Document", back_populates="folder")
    subfolders = relationship("Folder", backref="parent", remote_side=[id])


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="indexing")  # indexing, ready, failed
    s3_key = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")
    folder = relationship("Folder", back_populates="documents")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)  # list of source citation dicts
    
    # Latency / Token metrics
    embedding_time_ms = Column(Float, nullable=True)
    retrieval_time_ms = Column(Float, nullable=True)
    llm_time_ms = Column(Float, nullable=True)
    total_time_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", cascade="all, delete-orphan", uselist=False)


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("chat_messages.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 for thumb-up, -1 for thumb-down, or a scale
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("ChatMessage", back_populates="feedback")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # login, upload_pdf, chat_query, etc.
    endpoint = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    token_usage = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analytics")
