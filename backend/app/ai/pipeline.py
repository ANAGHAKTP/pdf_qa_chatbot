import os
import pickle
import uuid
from typing import List, Dict, Any, Tuple
import numpy as np

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

from app.core.config import settings

# In-memory parent document cache or disk-based cache folder
PARENTS_DIR = "./data/parents"
BM25_DIR = "./data/bm25"
os.makedirs(PARENTS_DIR, exist_ok=True)
os.makedirs(BM25_DIR, exist_ok=True)


def get_chroma_client():
    # Connect to local ChromaDB running as standalone or client
    # In docker, it connects to settings.CHROMADB_HOST
    # During testing, we use FakeEmbeddings to prevent network calls/401 auth errors
    if os.getenv("DB_NAME") == "docmind_test" or not settings.NVIDIA_API_KEY or "your-actual" in settings.NVIDIA_API_KEY:
        from langchain_core.embeddings import FakeEmbeddings
        embeddings = FakeEmbeddings(size=1024)
    else:
        embeddings = NVIDIAEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.NVIDIA_API_KEY
        )
    
    # Check if we should use HTTP client or local persistent folder
    if os.getenv("CHROMADB_HOST") in [None, "localhost", "127.0.0.1"] and not os.getenv("RUNNING_IN_DOCKER"):
        return Chroma(
            persist_directory="./data/chroma_db",
            embedding_function=embeddings
        )
    else:
        # Standalone Chroma server
        from chromadb import HttpClient
        return Chroma(
            client=HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT),
            embedding_function=embeddings
        )


def ingest_document_pipeline(doc_id: int, file_bytes: bytes) -> int:
    """
    Parses PDF, caches parent pages, splits into child chunks, 
    embeds child chunks to Chroma, and builds/saves BM25 index.
    """
    # Write temp file to read via PyPDFLoader
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        pages = loader.load()
    except Exception as pdf_err:
        print(f"⚠️ PyPDFLoader failed: {pdf_err}. Attempting raw text loading fallback.")
        from langchain_core.documents import Document as LC_Document
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = str(file_bytes)
        pages = [LC_Document(page_content=text, metadata={"source": tmp_path})]
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Save parent pages to disk
    doc_parents = {}
    for page_idx, page in enumerate(pages):
        page_num = page_idx + 1
        doc_parents[str(page_num)] = page.page_content
        
    with open(os.path.join(PARENTS_DIR, f"{doc_id}.pkl"), "wb") as f:
        pickle.dump(doc_parents, f)

    # Create child chunks (smaller size for precise retrieval)
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=100)
    
    child_docs = []
    chunk_texts = []
    
    for page_idx, page in enumerate(pages):
        page_num = page_idx + 1
        page_chunks = splitter.split_text(page.page_content)
        
        for chunk_idx, text in enumerate(page_chunks):
            metadata = {
                "doc_id": doc_id,
                "page": page_num,
                "chunk_idx": chunk_idx,
                "parent_key": f"{doc_id}_{page_num}"
            }
            child_docs.append((text, metadata))
            chunk_texts.append(text)

    if not child_docs:
        return 0

    # Add child chunks to Chroma
    vectorstore = get_chroma_client()
    texts = [c[0] for c in child_docs]
    metadatas = [c[1] for c in child_docs]
    ids = [f"{doc_id}_{meta['page']}_{meta['chunk_idx']}" for meta in metadatas]
    
    vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    # Build and save BM25 Sparse Index
    # Tokenize corpus for BM25
    tokenized_corpus = [text.lower().split() for text in chunk_texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # Save BM25 index along with chunk texts and metadatas
    bm25_data = {
        "bm25": bm25,
        "texts": chunk_texts,
        "metadatas": metadatas
    }
    with open(os.path.join(BM25_DIR, f"{doc_id}.pkl"), "wb") as f:
        pickle.dump(bm25_data, f)

    return len(child_docs)


def remove_document_embeddings(doc_id: int):
    """Deletes document chunks from Chroma and index files from disk."""
    try:
        vectorstore = get_chroma_client()
        # Chroma allows deleting by metadata filters
        vectorstore.delete(where={"doc_id": doc_id})
    except Exception as e:
        print(f"⚠️ Chroma deletion error: {e}")

    # Remove files from disk
    parent_file = os.path.join(PARENTS_DIR, f"{doc_id}.pkl")
    bm25_file = os.path.join(BM25_DIR, f"{doc_id}.pkl")
    
    if os.path.exists(parent_file):
        os.remove(parent_file)
    if os.path.exists(bm25_file):
        os.remove(bm25_file)


# ── Advanced Retrieval Pipeline ───────────────────────────────────────────────

def expand_queries(query: str) -> List[str]:
    """Generates alternative search queries for Multi-Query Expansion."""
    queries = [query]
    if not settings.NVIDIA_API_KEY:
        return queries
        
    try:
        llm = ChatNVIDIA(
            model=settings.LLM_MODEL,
            api_key=settings.NVIDIA_API_KEY,
            temperature=0.2
        )
        prompt = (
            f"You are an information retrieval assistant. Generate exactly 3 alternative search queries "
            f"for the user prompt: '{query}'.\n"
            f"Provide only the alternative queries, one per line. Do not number them."
        )
        response = llm.invoke(prompt)
        alternatives = [line.strip() for line in response.content.split("\n") if line.strip()]
        # Filter out numbers/bullets if any
        clean_alternatives = []
        for alt in alternatives:
            clean = alt.lstrip("0123456789.-*• ")
            if clean:
                clean_alternatives.append(clean)
        queries.extend(clean_alternatives[:3])
    except Exception as e:
        print(f"⚠️ Query expansion warning: {e}")
        
    return list(set(queries))


def dense_retrieval(queries: List[str], doc_ids: List[int], k: int = 15) -> List[Dict[str, Any]]:
    """Retrieves chunks from Chroma DB using MMR across multiple query expansions."""
    vectorstore = get_chroma_client()
    results = []
    seen_ids = set()
    
    filter_dict = {"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": doc_ids}}
    
    for q in queries:
        try:
            # Max Marginal Relevance for diverse chunks
            docs_with_scores = vectorstore.max_marginal_relevance_search(
                query=q,
                k=k,
                fetch_k=k * 3,
                filter=filter_dict
            )
            
            for doc in docs_with_scores:
                page = doc.metadata.get("page")
                chunk_idx = doc.metadata.get("chunk_idx")
                doc_id = doc.metadata.get("doc_id")
                unique_id = f"{doc_id}_{page}_{chunk_idx}"
                
                if unique_id not in seen_ids:
                    seen_ids.add(unique_id)
                    results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": 0.5  # placeholder score for dense MMR
                    })
        except Exception as e:
            print(f"⚠️ Dense retrieval warning for query '{q}': {e}")
            
    return results


def sparse_retrieval(query: str, doc_ids: List[int], k: int = 10) -> List[Dict[str, Any]]:
    """Retrieves top matches using BM25 across allowed documents."""
    results = []
    
    for doc_id in doc_ids:
        bm25_file = os.path.join(BM25_DIR, f"{doc_id}.pkl")
        if not os.path.exists(bm25_file):
            continue
            
        try:
            with open(bm25_file, "rb") as f:
                data = pickle.load(f)
                
            bm25 = data["bm25"]
            texts = data["texts"]
            metadatas = data["metadatas"]
            
            tokenized_query = query.lower().split()
            scores = bm25.get_scores(tokenized_query)
            top_indices = np.argsort(scores)[::-1][:k]
            
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append({
                        "content": texts[idx],
                        "metadata": metadatas[idx],
                        "score": float(scores[idx])
                    })
        except Exception as e:
            print(f"⚠️ BM25 retrieval error for doc {doc_id}: {e}")
            
    return results


def hybrid_search(query: str, doc_ids: List[int], dense_k: int = 15, sparse_k: int = 10) -> List[Dict[str, Any]]:
    """Combines Dense Search and Sparse BM25 using Reciprocal Rank Fusion (RRF)."""
    # 1. Expand queries
    queries = expand_queries(query)
    
    # 2. Get dense candidates
    dense_candidates = dense_retrieval(queries, doc_ids, k=dense_k)
    
    # 3. Get sparse candidates
    sparse_candidates = sparse_retrieval(query, doc_ids, k=sparse_k)
    
    # Reciprocal Rank Fusion
    rrf_scores = {}
    candidate_map = {}
    
    def get_key(cand):
        m = cand["metadata"]
        return f"{m['doc_id']}_{m['page']}_{m['chunk_idx']}"
        
    # Rank candidates
    for rank, cand in enumerate(dense_candidates):
        key = get_key(cand)
        rrf_scores[key] = rrf_scores.get(key, 0) + (1.0 / (rank + 60.0))  # standard RRF constant
        candidate_map[key] = cand
        
    for rank, cand in enumerate(sparse_candidates):
        key = get_key(cand)
        rrf_scores[key] = rrf_scores.get(key, 0) + (1.0 / (rank + 60.0))
        if key not in candidate_map:
            candidate_map[key] = cand
            
    # Sort by RRF score
    sorted_keys = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    fused_candidates = [candidate_map[k] for k in sorted_keys]
    
    return fused_candidates[:20]  # Return top 20 candidate chunks for re-ranking


def rerank_chunks(query: str, chunks: List[Dict[str, Any]], api_key: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Re-ranks chunks using Cross-Encoder.
    Uses NVIDIA NIM Reranking API if available. Otherwise falls back to local sentence-transformers.
    """
    if not chunks:
        return []
        
    if api_key and settings.RERANK_MODEL:
        try:
            # Use NVIDIA NIM re-ranker API
            import requests
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "accept": "application/json"
            }
            # NVIDIA NIM API format for reranking
            payload = {
                "model": settings.RERANK_MODEL,
                "query": {"text": query},
                "documents": [{"text": c["content"]} for c in chunks]
            }
            # URL for nvidia nim reranking
            url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking"
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                rankings = response.json().get("rankings", [])
                ranked_chunks = []
                for item in rankings[:k]:
                    idx = item["index"]
                    score = item["logit"]  # logit/confidence score
                    cand = chunks[idx]
                    cand["score"] = float(score)
                    ranked_chunks.append(cand)
                return ranked_chunks
        except Exception as e:
            print(f"⚠️ NVIDIA NIM re-ranking failed, falling back to local sentence-transformer: {e}")

    # Fallback: Local SentenceTransformers Cross-Encoder
    try:
        from sentence_transformers import CrossEncoder
        # Lazy load model
        model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [[query, c["content"]] for c in chunks]
        scores = model.predict(pairs)
        
        for idx, score in enumerate(scores):
            chunks[idx]["score"] = float(score)
            
        ranked_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
        return ranked_chunks[:k]
    except Exception as e:
        print(f"⚠️ Local re-ranking failed, returning top k original: {e}")
        return chunks[:k]


def load_parent_content(doc_id: int, page_num: int) -> str:
    """Loads parent page context for Parent Document Retrieval."""
    parent_file = os.path.join(PARENTS_DIR, f"{doc_id}.pkl")
    if os.path.exists(parent_file):
        try:
            with open(parent_file, "rb") as f:
                pages = pickle.load(f)
            return pages.get(str(page_num), "")
        except Exception:
            pass
    return ""


def advanced_rag_pipeline(
    query: str,
    doc_ids: List[int],
    api_key: str,
    k: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Main orchestration function for Advanced RAG.
    Returns (contexts_for_llm, citation_metadata).
    """
    # 1. Hybrid Search + RRF rank
    fused_candidates = hybrid_search(query, doc_ids)
    
    # 2. Cross-Encoder Re-rank
    top_chunks = rerank_chunks(query, fused_candidates, api_key, k=k)
    
    contexts = []
    citations = []
    
    for idx, chunk in enumerate(top_chunks):
        m = chunk["metadata"]
        doc_id = m["doc_id"]
        page_num = m["page"]
        
        # Parent Document Retrieval: Load full page text for context
        parent_text = load_parent_content(doc_id, page_num)
        context_text = parent_text if parent_text else chunk["content"]
        
        # Soft normalized score for frontend (sigmoid of cross encoder logit)
        score_val = chunk["score"]
        conf_score = float(1.0 / (1.0 + np.exp(-score_val))) if score_val is not None else 0.8
        
        contexts.append({
            "text": context_text,
            "doc_id": doc_id,
            "page": page_num
        })
        
        citations.append({
            "citation_num": idx + 1,
            "doc_id": doc_id,
            "page": page_num,
            "chunk_idx": m["chunk_idx"],
            "score": round(conf_score, 4),
            "highlighted_paragraph": chunk["content"]
        })
        
    return contexts, citations
