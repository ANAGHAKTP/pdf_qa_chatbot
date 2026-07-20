import math
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class RetrievalMetricsResult:
    recall_at_k: float
    precision_at_k: float
    mrr: float
    ndcg: float
    hit_rate: float
    context_recall: float
    context_precision: float
    chunk_recall: float
    chunk_precision: float
    doc_recall: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RetrievalEvaluator:
    """
    Computes retrieval quality metrics (Recall@K, Precision@K, MRR, NDCG, Hit Rate, Context Recall, Context Precision).
    """

    @classmethod
    def evaluate(
        cls,
        retrieved_chunks: List[Dict[str, Any]],
        expected_citations: List[Dict[str, Any]],
        k: int = 5
    ) -> RetrievalMetricsResult:
        if not expected_citations:
            return RetrievalMetricsResult(
                recall_at_k=1.0, precision_at_k=1.0, mrr=1.0, ndcg=1.0,
                hit_rate=1.0, context_recall=1.0, context_precision=1.0,
                chunk_recall=1.0, chunk_precision=1.0, doc_recall=1.0
            )

        top_k = retrieved_chunks[:k]
        relevant_matches = 0
        first_relevant_rank = 0
        dcg = 0.0
        idcg = 0.0

        for rank, chunk in enumerate(top_k, start=1):
            chunk_page = chunk.get("page")
            chunk_text = chunk.get("text", "").lower()

            is_relevant = False
            for exp in expected_citations:
                exp_page = exp.get("page")
                exp_kw = exp.get("keyword", "").lower()
                if exp_page and chunk_page == exp_page:
                    is_relevant = True
                elif exp_kw and exp_kw in chunk_text:
                    is_relevant = True

            if is_relevant:
                relevant_matches += 1
                if first_relevant_rank == 0:
                    first_relevant_rank = rank
                dcg += 1.0 / math.log2(rank + 1)

        # Compute IDCG
        for rank in range(1, min(len(expected_citations), k) + 1):
            idcg += 1.0 / math.log2(rank + 1)

        recall_at_k = round(relevant_matches / len(expected_citations), 4)
        precision_at_k = round(relevant_matches / max(len(top_k), 1), 4)
        mrr = round(1.0 / first_relevant_rank, 4) if first_relevant_rank > 0 else 0.0
        ndcg = round(dcg / idcg, 4) if idcg > 0 else 0.0
        hit_rate = 1.0 if relevant_matches > 0 else 0.0

        return RetrievalMetricsResult(
            recall_at_k=recall_at_k,
            precision_at_k=precision_at_k,
            mrr=mrr,
            ndcg=ndcg,
            hit_rate=hit_rate,
            context_recall=recall_at_k,
            context_precision=precision_at_k,
            chunk_recall=recall_at_k,
            chunk_precision=precision_at_k,
            doc_recall=hit_rate
        )
