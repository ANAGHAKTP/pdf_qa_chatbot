import re
from typing import List, Dict, Any, Tuple
from app.ai.citation_engine import CitationItem
from app.ai.confidence import ConfidenceReport, ConfidenceLevel

class HallucinationGuard:
    """
    HallucinationGuard module responsible for:
    - Validating evidence sufficiency
    - Lowering confidence when context is weak or missing
    - Adding user warning notices for ungrounded or low-confidence responses
    - Stripping fabricated citation links
    """

    @staticmethod
    def validate_response(
        response_text: str,
        citations: List[CitationItem],
        confidence_report: ConfidenceReport
    ) -> Tuple[str, ConfidenceReport, List[str]]:
        warnings: List[str] = []
        validated_text = response_text
        updated_report = confidence_report

        # 1. Evidence sufficiency check
        if not citations or confidence_report.retrieval_score < 0.35:
            # Insufficient evidence
            updated_report = ConfidenceReport(
                level=ConfidenceLevel.LOW,
                score=min(confidence_report.score, 0.30),
                retrieval_score=confidence_report.retrieval_score,
                reranker_score=confidence_report.reranker_score,
                citation_coverage=0.0,
                context_consistency=confidence_report.context_consistency
            )
            warnings.append(
                "⚠️ Warning: Retrieved evidence is limited or weak. Please verify key claims against original documents."
            )

        # 2. Check for fabricated citation numbers in LLM text (e.g., [99] when only 2 citations exist)
        max_valid_citation = len(citations)
        def fix_citation(match):
            num = int(match.group(1))
            if num > max_valid_citation:
                return ""  # Remove invalid citation link
            return match.group(0)

        validated_text = re.sub(r"\[(\d+)\]", fix_citation, validated_text)

        # If warnings exist and low confidence, prepend warning note if not already present
        if updated_report.level == ConfidenceLevel.LOW and warnings:
            warning_header = warnings[0]
            if warning_header not in validated_text and "cannot find the answer" not in validated_text.lower():
                validated_text = f"{warning_header}\n\n{validated_text}"

        return validated_text, updated_report, warnings
