import os
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_embeddings():
    if os.getenv("DB_NAME") == "docmind_test" or not settings.NVIDIA_API_KEY or "your-actual" in settings.NVIDIA_API_KEY:
        from langchain_core.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=1024)
    else:
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        return NVIDIAEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.NVIDIA_API_KEY
        )


def get_qdrant_client():
    """Connects to Qdrant Cloud cluster or in-memory Qdrant instance for testing."""
    import qdrant_client
    from langchain_qdrant import QdrantVectorStore

    embeddings = get_embeddings()
    collection_name = getattr(settings, "QDRANT_COLLECTION", "docmind_chunks")

    if settings.QDRANT_URL:
        client = qdrant_client.QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
    else:
        # Fallback to local in-memory instance for testing/local execution without Qdrant Cloud credentials
        client = qdrant_client.QdrantClient(location=":memory:")

    # Ensure collection exists
    from qdrant_client.http import models
    try:
        client.get_collection(collection_name=collection_name)
    except Exception:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1024,
                distance=models.Distance.COSINE
            )
        )

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings
    )


def load_parent_content(doc_id: int, page_num: int, db: Optional[Session] = None) -> str:
    """Loads full parent page text from database or optional session."""
    if db is not None:
        try:
            from app.db.models import DocumentPage
            page_obj = db.query(DocumentPage).filter(
                DocumentPage.doc_id == doc_id,
                DocumentPage.page_num == page_num
            ).first()
            if page_obj and page_obj.text:
                return page_obj.text
        except Exception as e:
            logger.warning(f"Could not load page from DB: {e}")

    # Standalone query fallback if db session was not passed
    try:
        from app.db.session import SessionLocal
        with SessionLocal() as session:
            from app.db.models import DocumentPage
            page_obj = session.query(DocumentPage).filter(
                DocumentPage.doc_id == doc_id,
                DocumentPage.page_num == page_num
            ).first()
            if page_obj and page_obj.text:
                return page_obj.text
    except Exception:
        pass

    return ""
