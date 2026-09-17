import os
import pickle
import time
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from app.core.config import settings
from app.ai.common import get_qdrant_client, load_parent_content
from app.ai.query_processor import QueryProcessor, ProcessedQuery
from app.ai.retriever import DenseRetriever, BM25Retriever, PostgreSQLFTSRetriever, ReciprocalRankFusion, CrossEncoderReranker
from app.ai.context_builder import ContextBuilder, ContextResult
from app.ai.citation_engine import CitationEngine, CitationItem
from app.ai.confidence import ConfidenceEstimator, ConfidenceReport, ConfidenceLevel
from app.ai.hallucination_guard import HallucinationGuard

logger = logging.getLogger(__name__)


def ingest_document_pipeline(doc_id: int, file_bytes: bytes, filename: str = "document.pdf") -> int:
    """Ingests PDF document via Modular Ingestion Pipeline."""
    from app.ai.ingestion.pipeline import ModularIngestionPipeline
    pipeline = ModularIngestionPipeline()
    res = pipeline.process_and_index(doc_id, filename, file_bytes)
    return res["chunk_count"]


def remove_document_embeddings(doc_id: int):
    """Deletes document chunks from Qdrant Cloud and PostgreSQL database."""
    # 1. Qdrant point deletion
    try:
        vectorstore = get_qdrant_client()
        from qdrant_client.http import models
        vectorstore.client.delete(
            collection_name=getattr(settings, "QDRANT_COLLECTION", "docmind_chunks"),
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[models.FieldCondition(key="metadata.doc_id", match=models.MatchValue(value=doc_id))]
                )
            )
        )
    except Exception as e:
        logger.warning(f"Qdrant deletion error for doc {doc_id}: {e}")

    # 2. Database cleanup of DocumentChunk and DocumentPage rows
    try:
        from app.db.session import SessionLocal
        from app.db.models import DocumentChunk, DocumentPage
        with SessionLocal() as db:
            db.query(DocumentChunk).filter(DocumentChunk.doc_id == doc_id).delete(synchronize_session=False)
            db.query(DocumentPage).filter(DocumentPage.doc_id == doc_id).delete(synchronize_session=False)
            db.commit()
    except Exception as db_err:
        logger.warning(f"DB chunk/page deletion error for doc {doc_id}: {db_err}")


# ── AI Answer Pipeline & Orchestration ────────────────────────────────────────

class AnswerPipeline:
    """
    Dedicated AI Intelligence Pipeline Orchestrator:
    Query -> QueryProcessor -> Retriever -> Reranker -> ContextBuilder -> CitationEngine -> ConfidenceEstimator
    """

    def __init__(self, token_budget: int = 3000):
        self.query_processor = QueryProcessor()
        self.dense_retriever = DenseRetriever(k=15)
        self.bm25_retriever = BM25Retriever(k=10)
        self.rrf = ReciprocalRankFusion(rrf_k=60.0)
        self.reranker = CrossEncoderReranker(top_k=5)
        self.context_builder = ContextBuilder(max_token_budget=token_budget)

    def execute(
        self,
        query: str,
        doc_ids: List[int],
        api_key: str,
        doc_map: Optional[Dict[int, str]] = None
    ) -> Dict[str, Any]:
        query_id = str(uuid.uuid4())
        stage_timings = {}

        # 1. Query Processing
        t0 = time.time()
        processed_query: ProcessedQuery = self.query_processor.process(query)
        stage_timings["query_processing_ms"] = round((time.time() - t0) * 1000, 2)

        # 2. Retrieval Phase
        t1 = time.time()
        dense_candidates = self.dense_retriever.retrieve(
            processed_query.expanded_queries,
            doc_ids,
            processed_query.metadata_filters
        )
        sparse_candidates = self.bm25_retriever.retrieve(
            processed_query.normalized_query,
            doc_ids
        )
        fused_candidates = self.rrf.merge(dense_candidates, sparse_candidates, top_n=20)
        stage_timings["retrieval_ms"] = round((time.time() - t1) * 1000, 2)

        # 3. Re-ranking Phase
        t2 = time.time()
        reranked_chunks = self.reranker.rerank(processed_query.normalized_query, fused_candidates, api_key)
        stage_timings["reranker_ms"] = round((time.time() - t2) * 1000, 2)

        # 4. Context Building
        t3 = time.time()
        context_result: ContextResult = self.context_builder.build_context(reranked_chunks, doc_map)
        stage_timings["context_building_ms"] = round((time.time() - t3) * 1000, 2)

        # 5. Citation Generation
        t4 = time.time()
        citations: List[CitationItem] = CitationEngine.generate_citations(context_result.chunks, doc_map)
        stage_timings["citation_engine_ms"] = round((time.time() - t4) * 1000, 2)

        # 6. Initial Confidence Estimation
        confidence_report: ConfidenceReport = ConfidenceEstimator.estimate(citations)

        # Structured non-content logging
        logger.info(
            f"RAG Pipeline Executed | query_id={query_id} | "
            f"retrieval_latency_ms={stage_timings['retrieval_ms']} | "
            f"reranker_latency_ms={stage_timings['reranker_ms']} | "
            f"documents_retrieved={len(reranked_chunks)} | "
            f"citations_returned={len(citations)} | "
            f"confidence_level={confidence_report.level.value} | "
            f"confidence_score={confidence_report.score}"
        )

        return {
            "query_id": query_id,
            "processed_query": processed_query,
            "context_result": context_result,
            "citations": citations,
            "confidence_report": confidence_report,
            "stage_timings": stage_timings
        }


# Backward-compatibility wrapper for existing service calls
def advanced_rag_pipeline(
    query: str,
    doc_ids: List[int],
    api_key: str,
    k: int = 5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Legacy backward-compatibility function wrapping AnswerPipeline."""
    pipeline = AnswerPipeline()
    result = pipeline.execute(query, doc_ids, api_key)
    
    contexts = []
    for chunk in result["context_result"].chunks:
        contexts.append({
            "text": chunk.text,
            "doc_id": chunk.doc_id,
            "page": chunk.page
        })

    citations = [cit.to_dict() for cit in result["citations"]]
    return contexts, citations
