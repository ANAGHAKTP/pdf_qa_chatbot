import os
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
from app.core.config import settings
from app.ai.common import get_chroma_client, BM25_DIR

class DenseRetriever:
    """Stage 1: Vector similarity / MMR retrieval from ChromaDB."""
    
    def __init__(self, k: int = 15):
        self.k = k

    def retrieve(self, queries: List[str], doc_ids: List[int], metadata_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not queries or not doc_ids:
            return []

        vectorstore = get_chroma_client()
        results = []
        seen_ids = set()

        base_filter = {"doc_id": doc_ids[0]} if len(doc_ids) == 1 else {"doc_id": {"$in": doc_ids}}
        if metadata_filters:
            # Merge extra filters like page
            merged_filter = {**base_filter}
            for key, val in metadata_filters.items():
                merged_filter[key] = val
            filter_dict = merged_filter
        else:
            filter_dict = base_filter

        for q in queries:
            try:
                docs_with_scores = vectorstore.max_marginal_relevance_search(
                    query=q,
                    k=self.k,
                    fetch_k=self.k * 3,
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
                            "score": 0.5,
                            "retrieval_type": "dense"
                        })
            except Exception as e:
                pass

        return results


class BM25Retriever:
    """Stage 2: BM25 Lexical Keyword search across disk indices."""
    
    def __init__(self, k: int = 10):
        self.k = k

    def retrieve(self, query: str, doc_ids: List[int]) -> List[Dict[str, Any]]:
        if not query or not doc_ids:
            return []

        results = []
        tokenized_query = query.lower().split()

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

                scores = bm25.get_scores(tokenized_query)
                top_indices = np.argsort(scores)[::-1][:self.k]

                for idx in top_indices:
                    if scores[idx] > 0:
                        results.append({
                            "content": texts[idx],
                            "metadata": metadatas[idx],
                            "score": float(scores[idx]),
                            "retrieval_type": "bm25"
                        })
            except Exception as e:
                pass

        return results


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
