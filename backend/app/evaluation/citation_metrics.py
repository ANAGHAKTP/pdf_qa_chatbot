from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class CitationEvaluationResult:
    citation_accuracy: float
    citation_precision: float
    citation_recall: float
    wrong_citation_rate: float
    missing_citation_rate: float
    hallucinated_citation_rate: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CitationEvaluator:
    """
    Evaluates citation validity, precision, recall, and hallucination rates.
    """

    @classmethod
    def evaluate(
        cls,
        generated_citations: List[Dict[str, Any]],
        expected_citations: List[Dict[str, Any]]
    ) -> CitationEvaluationResult:
        if not expected_citations and not generated_citations:
            return CitationEvaluationResult(
                citation_accuracy=1.0, citation_precision=1.0, citation_recall=1.0,
                wrong_citation_rate=0.0, missing_citation_rate=0.0, hallucinated_citation_rate=0.0
            )

        if not expected_citations and generated_citations:
            return CitationEvaluationResult(
                citation_accuracy=0.0, citation_precision=0.0, citation_recall=1.0,
                wrong_citation_rate=1.0, missing_citation_rate=0.0, hallucinated_citation_rate=1.0
            )

        correct_citations = 0
        hallucinated_citations = 0

        for gen_cit in generated_citations:
            gen_page = gen_cit.get("page")
            matched = False
            for exp_cit in expected_citations:
                exp_page = exp_cit.get("page")
                if exp_page and gen_page == exp_page:
                    matched = True
                    break
            if matched:
                correct_citations += 1
            else:
                hallucinated_citations += 1

        precision = round(correct_citations / max(len(generated_citations), 1), 4)
        recall = round(correct_citations / max(len(expected_citations), 1), 4)
        accuracy = round((precision + recall) / 2.0, 4)
        hallucination_rate = round(hallucinated_citations / max(len(generated_citations), 1), 4)
        missing_rate = round(max(0, len(expected_citations) - correct_citations) / len(expected_citations), 4)

        return CitationEvaluationResult(
            citation_accuracy=accuracy,
            citation_precision=precision,
            citation_recall=recall,
            wrong_citation_rate=hallucination_rate,
            missing_citation_rate=missing_rate,
            hallucinated_citation_rate=hallucination_rate
        )
