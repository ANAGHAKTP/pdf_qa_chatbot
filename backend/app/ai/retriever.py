import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy import func
from app.core.config import settings
from app.ai.common import get_qdrant_client

logger = logging.getLogger(__name__)


class DenseRetriever:
    """Stage 1: Vector similarity / MMR retrieval from Qdrant Cloud."""
    
    def __init__(self, k: int = 15):
        self.k = k

    def retrieve(self, queries: List[str], doc_ids: List[int], metadata_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not queries or not doc_ids:
            return []

        results = []
        seen_ids = set()

        try:
            vectorstore = get_qdrant_client()
            from qdrant_client.http import models

            if len(doc_ids) == 1:
                must_conditions = [
                    models.FieldCondition(key="metadata.doc_id", match=models.MatchValue(value=doc_ids[0]))
                ]
            else:
                must_conditions = [
                    models.FieldCondition(key="metadata.doc_id", match=models.MatchAny(any=doc_ids))
                ]

            if metadata_filters:
                for k, v in metadata_filters.items():
                    must_conditions.append(
                        models.FieldCondition(key=f"metadata.{k}", match=models.MatchValue(value=v))
                    )

            qdrant_filter = models.Filter(must=must_conditions)

            for q in queries:
                try:
                    docs = vectorstore.max_marginal_relevance_search(
                        query=q,
                        k=self.k,
                        fetch_k=self.k * 3,
                        filter=qdrant_filter
                    )
                    for doc in docs:
                        meta = doc.metadata or {}
                        page = meta.get("page", 1)
                        chunk_idx = meta.get("chunk_idx", 0)
                        d_id = meta.get("doc_id", doc_ids[0])
                        unique_id = f"{d_id}_{page}_{chunk_idx}"

                        if unique_id not in seen_ids:
                            seen_ids.add(unique_id)
                            results.append({
                                "content": doc.page_content,
                                "metadata": meta,
                                "score": 0.5,
                                "retrieval_type": "dense"
                            })
                except Exception as inner_e:
                    logger.warning(f"Dense retrieval query failed for query '{q}': {inner_e}")
        except Exception as e:
            logger.error(f"DenseRetriever failed: {e}")

        return results


class PostgreSQLFTSRetriever:
    """Stage 2: PostgreSQL Full-Text Search (Lexical Keyword Search)."""
    
    def __init__(self, k: int = 10):
        self.k = k

    def retrieve(self, query: str, doc_ids: List[int]) -> List[Dict[str, Any]]:
        if not query or not doc_ids:
            return []

        results = []
        try:
            from app.db.session import SessionLocal
            from app.db.models import DocumentChunk

            with SessionLocal() as db:
                # 1. Primary PostgreSQL FTS query using tsvector and websearch_to_tsquery
                try:
                    ts_query = func.websearch_to_tsquery('english', query)
                    rank_func = func.ts_rank_cd(DocumentChunk.search_vector, ts_query)

                    chunks = db.query(DocumentChunk, rank_func.label("rank")).filter(
                        DocumentChunk.doc_id.in_(doc_ids),
                        DocumentChunk.search_vector.op("@@")(ts_query)
                    ).order_by(rank_func.desc()).limit(self.k).all()

                    for chunk_row, rank in chunks:
                        meta = chunk_row.metadata_json or {
                            "doc_id": chunk_row.doc_id,
                            "page": chunk_row.page,
                            "chunk_idx": chunk_row.chunk_idx,
                            "chunk_id": chunk_row.chunk_id,
                            "parent_section": chunk_row.parent_section
                        }
                        results.append({
                            "content": chunk_row.content,
                            "metadata": meta,
                            "score": float(rank) if rank else 0.5,
                            "retrieval_type": "lexical"
                        })
                except Exception as fts_err:
                    logger.warning(f"PostgreSQL FTS query failed, using ILIKE fallback: {fts_err}")
                    # Fallback ILIKE text search if FTS query encounters error
                    words = [w for w in query.lower().split() if len(w) > 2]
                    if words:
                        from sqlalchemy import or_
                        filters = [DocumentChunk.content.ilike(f"%{w}%") for w in words[:3]]
                        chunks = db.query(DocumentChunk).filter(
                            DocumentChunk.doc_id.in_(doc_ids),
                            or_(*filters)
                        ).limit(self.k).all()

                        for chunk_row in chunks:
                            meta = chunk_row.metadata_json or {
                                "doc_id": chunk_row.doc_id,
                                "page": chunk_row.page,
                                "chunk_idx": chunk_row.chunk_idx,
                                "chunk_id": chunk_row.chunk_id,
                                "parent_section": chunk_row.parent_section
                            }
                            results.append({
                                "content": chunk_row.content,
                                "metadata": meta,
                                "score": 0.4,
                                "retrieval_type": "lexical"
                            })
        except Exception as e:
            logger.error(f"PostgreSQLFTSRetriever failed: {e}")

        return results


# Backward compatibility alias
BM25Retriever = PostgreSQLFTSRetriever


class ReciprocalRankFusion:
    """Stage 3: Combines Dense and BM25 candidate lists using RRF scoring."""
    
    def __init__(self, rrf_k: float = 60.0):
        self.rrf_k = rrf_k

    def merge(self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
        rrf_scores: Dict[str, float] = {}
        candidate_map: Dict[str, Dict[str, Any]] = {}

        def get_key(cand):
            m = cand["metadata"]
            return f"{m['doc_id']}_{m['page']}_{m['chunk_idx']}"

        for rank, cand in enumerate(dense_results):
            key = get_key(cand)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rank + self.rrf_k))
            candidate_map[key] = cand

        for rank, cand in enumerate(sparse_results):
            key = get_key(cand)
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (rank + self.rrf_k))
            if key not in candidate_map:
                candidate_map[key] = cand

        sorted_keys = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        fused = [candidate_map[k] for k in sorted_keys]
        for k, cand in candidate_map.items():
            cand["rrf_score"] = rrf_scores[k]

        return fused[:top_n]


class CrossEncoderReranker:
    """Stage 4: Re-ranks candidate chunks using Cross-Encoder model or NVIDIA NIM API."""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    def rerank(self, query: str, candidate_chunks: List[Dict[str, Any]], api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        if not candidate_chunks:
            return []

        # 1. NVIDIA NIM Reranking API if available
        if api_key and settings.RERANK_MODEL and "stub" not in api_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "accept": "application/json"
                }
                payload = {
                    "model": settings.RERANK_MODEL,
                    "query": {"text": query},
                    "documents": [{"text": c["content"]} for c in candidate_chunks]
                }
                url = "https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking"
                response = requests.post(url, headers=headers, json=payload, timeout=5)
                if response.status_code == 200:
                    rankings = response.json().get("rankings", [])
                    ranked_chunks = []
                    for item in rankings[:self.top_k]:
                        idx = item["index"]
                        score = float(item["logit"])
                        cand = candidate_chunks[idx]
                        cand["rerank_score"] = score
                        cand["score"] = score
                        ranked_chunks.append(cand)
                    return ranked_chunks
            except Exception as e:
                pass

        # 2. Local CrossEncoder Fallback
        try:
            from sentence_transformers import CrossEncoder
            model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            pairs = [[query, c["content"]] for c in candidate_chunks]
            scores = model.predict(pairs)

            for idx, score in enumerate(scores):
                candidate_chunks[idx]["rerank_score"] = float(score)
                candidate_chunks[idx]["score"] = float(score)

            ranked = sorted(candidate_chunks, key=lambda x: x["rerank_score"], reverse=True)
            return ranked[:self.top_k]
        except Exception:
            # Final fallback: return top_k candidates by RRF order
            for c in candidate_chunks:
                if "score" not in c:
                    c["score"] = c.get("rrf_score", 0.5)
            return candidate_chunks[:self.top_k]
