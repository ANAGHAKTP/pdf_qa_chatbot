from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from app.ai.citation_engine import CitationItem

class ConfidenceLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class ConfidenceReport:
    level: ConfidenceLevel
    score: float
    retrieval_score: float
    reranker_score: float
    citation_coverage: float
    context_consistency: float

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        return d


class ConfidenceEstimator:
    """
    Estimates overall confidence of the generated answer based on:
    - Retrieval scores
    - Reranker scores
    - Citation coverage in response text
    - Context consistency across retrieved chunks
    """

    @staticmethod
    def estimate(
        citations: List[CitationItem],
        response_text: str = "",
        raw_scores: Optional[List[float]] = None
    ) -> ConfidenceReport:
        if not citations:
            return ConfidenceReport(
                level=ConfidenceLevel.LOW,
                score=0.0,
                retrieval_score=0.0,
                reranker_score=0.0,
                citation_coverage=0.0,
                context_consistency=0.0
            )

        # 1. Retrieval & Reranker Score Average
        scores = [c.score for c in citations]
        avg_score = float(sum(scores) / len(scores))
        max_score = float(max(scores))

        retrieval_score = round(max_score, 4)
        reranker_score = round(avg_score, 4)

        # 2. Citation Coverage Estimation
        # Check if citations like [1], [2] exist in response_text
        import re
        cites_found = set(re.findall(r"\[(\d+)\]", response_text))
        expected_cites = set(str(c.citation_num) for c in citations)
        
        if expected_cites:
            citation_coverage = round(len(cites_found.intersection(expected_cites)) / len(expected_cites), 4)
        else:
            citation_coverage = 1.0 if not response_text else 0.5

        # 3. Context Consistency
        # Variance of scores: low variance = consistent context retrieval
        if len(scores) > 1:
            variance = float(sum((s - avg_score) ** 2 for s in scores) / len(scores))
            context_consistency = round(max(0.0, 1.0 - (variance * 2)), 4)
        else:
            context_consistency = 1.0

        # Weighted final score calculation
        overall_score = round(
            (retrieval_score * 0.4) +
            (reranker_score * 0.3) +
            (citation_coverage * 0.2) +
            (context_consistency * 0.1),
            4
        )

        if overall_score >= 0.70:
            level = ConfidenceLevel.HIGH
        elif overall_score >= 0.45:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return ConfidenceReport(
            level=level,
            score=overall_score,
            retrieval_score=retrieval_score,
            reranker_score=reranker_score,
            citation_coverage=citation_coverage,
            context_consistency=context_consistency
        )
