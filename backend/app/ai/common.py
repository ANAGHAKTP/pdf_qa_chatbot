import os
import pickle
from app.core.config import settings

PARENTS_DIR = "./data/parents"
BM25_DIR = "./data/bm25"
os.makedirs(PARENTS_DIR, exist_ok=True)
os.makedirs(BM25_DIR, exist_ok=True)


def get_chroma_client():
    """Connects to local ChromaDB running standalone or client."""
    if os.getenv("DB_NAME") == "docmind_test" or not settings.NVIDIA_API_KEY or "your-actual" in settings.NVIDIA_API_KEY:
        from langchain_core.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(size=1024)
    else:
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        embeddings = NVIDIAEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.NVIDIA_API_KEY
        )
    
    if os.getenv("CHROMADB_HOST") in [None, "localhost", "127.0.0.1"] and not os.getenv("RUNNING_IN_DOCKER"):
        from langchain_chroma import Chroma
        return Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=embeddings
        )
    else:
        from langchain_chroma import Chroma
        from chromadb import HttpClient
        return Chroma(
            client=HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT),
            embedding_function=embeddings
        )


def load_parent_content(doc_id: int, page_num: int) -> str:
    """Loads full parent page text from disk cache."""
    parent_file = os.path.join(PARENTS_DIR, f"{doc_id}.pkl")
    if os.path.exists(parent_file):
        try:
            with open(parent_file, "rb") as f:
                pages = pickle.load(f)
            return pages.get(str(page_num), "")
        except Exception:
            pass
    return ""
