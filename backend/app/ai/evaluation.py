import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class EvaluationSample:
    query: str
    ground_truth_doc_ids: List[int]
    expected_keywords: List[str] = field(default_factory=list)


@dataclass
class EvaluationMetrics:
    total_samples: int
    retrieval_recall: float
    retrieval_precision: float
    citation_accuracy: float
    avg_retrieval_latency_ms: float
    avg_generation_latency_ms: float
    avg_token_usage: float
    avg_answer_length: float
    confidence_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvaluationFramework:
    """
    Evaluation Framework to measure and record:
    - Retrieval Recall
    - Retrieval Precision
    - Citation Accuracy
    - Average Retrieval Latency
    - Average Generation Latency
    - Token Usage
    - Answer Length
    - Confidence Distribution
    """

    @staticmethod
    def calculate_recall(retrieved_doc_ids: List[int], ground_truth_doc_ids: List[int]) -> float:
        if not ground_truth_doc_ids:
            return 1.0
        found = set(retrieved_doc_ids).intersection(set(ground_truth_doc_ids))
        return round(len(found) / len(set(ground_truth_doc_ids)), 4)

    @staticmethod
    def calculate_precision(retrieved_doc_ids: List[int], ground_truth_doc_ids: List[int]) -> float:
        if not retrieved_doc_ids:
            return 0.0
        found = set(retrieved_doc_ids).intersection(set(ground_truth_doc_ids))
        return round(len(found) / len(set(retrieved_doc_ids)), 4)

    @staticmethod
    def calculate_citation_accuracy(citations: List[Dict[str, Any]], expected_keywords: List[str]) -> float:
        if not citations or not expected_keywords:
            return 1.0
        matching = 0
        for cit in citations:
            text = cit.get("highlighted_paragraph", "").lower()
            if any(kw.lower() in text for kw in expected_keywords):
                matching += 1
        return round(matching / len(citations), 4)

    @classmethod
    def evaluate_results(cls, test_runs: List[Dict[str, Any]]) -> EvaluationMetrics:
        if not test_runs:
            return EvaluationMetrics(
                total_samples=0,
                retrieval_recall=0.0,
                retrieval_precision=0.0,
                citation_accuracy=0.0,
                avg_retrieval_latency_ms=0.0,
                avg_generation_latency_ms=0.0,
                avg_token_usage=0.0,
                avg_answer_length=0.0,
                confidence_distribution={"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            )

        n = len(test_runs)
        recalls = [run.get("recall", 1.0) for run in test_runs]
        precisions = [run.get("precision", 1.0) for run in test_runs]
        citation_accs = [run.get("citation_accuracy", 1.0) for run in test_runs]
        retr_latencies = [run.get("retrieval_latency_ms", 0.0) for run in test_runs]
        gen_latencies = [run.get("generation_latency_ms", 0.0) for run in test_runs]
        tokens = [run.get("token_count", 0) for run in test_runs]
        lengths = [run.get("answer_length", 0) for run in test_runs]

        conf_dist = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for run in test_runs:
            lvl = run.get("confidence_level", "MEDIUM")
            conf_dist[lvl] = conf_dist.get(lvl, 0) + 1

        return EvaluationMetrics(
            total_samples=n,
            retrieval_recall=round(float(sum(recalls) / n), 4),
            retrieval_precision=round(float(sum(precisions) / n), 4),
            citation_accuracy=round(float(sum(citation_accs) / n), 4),
            avg_retrieval_latency_ms=round(float(sum(retr_latencies) / n), 2),
            avg_generation_latency_ms=round(float(sum(gen_latencies) / n), 2),
            avg_token_usage=round(float(sum(tokens) / n), 1),
            avg_answer_length=round(float(sum(lengths) / n), 1),
            confidence_distribution=conf_dist
        )
