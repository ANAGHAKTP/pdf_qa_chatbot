import pytest
from app.ai.query_processor import QueryProcessor, ProcessedQuery
from app.ai.retriever import DenseRetriever, BM25Retriever, ReciprocalRankFusion, CrossEncoderReranker
from app.ai.context_builder import ContextBuilder, ContextChunk
from app.ai.citation_engine import CitationEngine, CitationItem
from app.ai.confidence import ConfidenceEstimator, ConfidenceLevel, ConfidenceReport
from app.ai.hallucination_guard import HallucinationGuard
from app.ai.evaluation import EvaluationFramework, EvaluationMetrics
from app.ai.pipeline import AnswerPipeline


def test_query_processor_normalization_and_keywords():
    raw_query = "   What are the   key financial obligations on page 5?   "
    processed = QueryProcessor.process(raw_query)

    assert processed.normalized_query == "What are the key financial obligations on page 5?"
    assert "financial" in [k.lower() for k in processed.keywords]
    assert "obligations" in [k.lower() for k in processed.keywords]
    assert processed.metadata_filters.get("page") == 5
    assert len(processed.expanded_queries) >= 1


def test_retriever_hybrid_rrf_merge():
    dense_results = [
        {"content": "Chunk A text", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 0}, "score": 0.9},
        {"content": "Chunk B text", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 1}, "score": 0.8},
    ]
    sparse_results = [
        {"content": "Chunk B text", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 1}, "score": 10.5},
        {"content": "Chunk C text", "metadata": {"doc_id": 1, "page": 2, "chunk_idx": 0}, "score": 8.2},
    ]

    rrf = ReciprocalRankFusion()
    merged = rrf.merge(dense_results, sparse_results, top_n=10)

    assert len(merged) == 3
    # Chunk B should rank highest because it appeared in both dense and sparse
    first_chunk_meta = merged[0]["metadata"]
    assert first_chunk_meta["chunk_idx"] == 1


def test_cross_encoder_reranker_fallback():
    candidates = [
        {"content": "Low relevance chunk", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 0}},
        {"content": "High relevance revenue growth document", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 1}}
    ]

    reranker = CrossEncoderReranker(top_k=2)
    ranked = reranker.rerank("revenue growth", candidates)

    assert len(ranked) == 2
    assert "score" in ranked[0]


def test_context_builder_deduplication_and_ordering():
    raw_chunks = [
        {"content": "Duplicate content snippet", "metadata": {"doc_id": 1, "page": 2, "chunk_idx": 0}, "score": 0.9},
        {"content": "Duplicate content snippet", "metadata": {"doc_id": 1, "page": 2, "chunk_idx": 0}, "score": 0.9},
        {"content": "First page snippet", "metadata": {"doc_id": 1, "page": 1, "chunk_idx": 0}, "score": 0.8},
    ]

    builder = ContextBuilder(max_token_budget=1000)
    result = builder.build_context(raw_chunks)

    assert result.deduped_count == 1
    assert len(result.chunks) == 2
    # Ensure ordered by page number (page 1 before page 2)
    assert result.chunks[0].page == 1
    assert result.chunks[1].page == 2


def test_citation_engine_formatting():
    chunks = [
        ContextChunk(
            text="The company generated $50M in Q3 revenue.",
            doc_id=101,
            page=4,
            chunk_idx=2,
            score=0.92
        )
    ]

    doc_map = {101: "Q3_Report.pdf"}
    citations = CitationEngine.generate_citations(chunks, doc_map)

    assert len(citations) == 1
    cit = citations[0]
    assert cit.citation_num == 1
    assert cit.filename == "Q3_Report.pdf"
    assert cit.page == 4
    assert cit.chunk_id == "101_4_2"
    assert cit.score > 0.0
    assert "preview_url" in cit.to_dict()


def test_confidence_estimator_and_hallucination_guard():
    chunks = [
        ContextChunk(
            text="The contract terminates on December 31, 2026.",
            doc_id=1,
            page=2,
            chunk_idx=1,
            score=0.88
        )
    ]

    citations = CitationEngine.generate_citations(chunks, {1: "Contract.pdf"})
    response_text = "The contract terminates on December 31, 2026 [1]."

    report = ConfidenceEstimator.estimate(citations, response_text)
    assert report.level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
    assert report.score >= 0.5

    # Test hallucination guard with zero citations
    empty_report = ConfidenceEstimator.estimate([])
    validated_text, guard_report, warnings = HallucinationGuard.validate_response(
        "Some ungrounded claim.",
        [],
        empty_report
    )

    assert guard_report.level == ConfidenceLevel.LOW
    assert len(warnings) > 0
    assert "Warning" in validated_text or "limited" in validated_text


def test_evaluation_framework_metrics():
    test_runs = [
        {
            "recall": 1.0,
            "precision": 0.8,
            "citation_accuracy": 1.0,
            "retrieval_latency_ms": 120.0,
            "generation_latency_ms": 300.0,
            "token_count": 150,
            "answer_length": 450,
            "confidence_level": "HIGH"
        },
        {
            "recall": 0.5,
            "precision": 0.5,
            "citation_accuracy": 0.75,
            "retrieval_latency_ms": 140.0,
            "generation_latency_ms": 350.0,
            "token_count": 180,
            "answer_length": 500,
            "confidence_level": "MEDIUM"
        }
    ]

    metrics = EvaluationFramework.evaluate_results(test_runs)

    assert metrics.total_samples == 2
    assert metrics.retrieval_recall == 0.75
    assert metrics.retrieval_precision == 0.65
    assert metrics.confidence_distribution["HIGH"] == 1
    assert metrics.confidence_distribution["MEDIUM"] == 1
    assert metrics.avg_retrieval_latency_ms == 130.0


def test_answer_pipeline_end_to_end(test_user):
    pipeline = AnswerPipeline()
    result = pipeline.execute(
        query="What are the key terms in the document?",
        doc_ids=[1],
        api_key="stub-key"
    )

    assert "query_id" in result
    assert "processed_query" in result
    assert "context_result" in result
    assert "citations" in result
    assert "confidence_report" in result
    assert "stage_timings" in result
    assert result["stage_timings"]["retrieval_ms"] >= 0
