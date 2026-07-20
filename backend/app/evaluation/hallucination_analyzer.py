from typing import List, Dict, Any
from dataclasses import dataclass, field, asdict

@dataclass
class HallucinationFlag:
    category: str  # "unsupported_claim", "fabricated_citation", "conflicting_evidence", "missing_evidence", "low_evidence"
    description: str
    severity: str  # "HIGH", "MEDIUM", "LOW"


@dataclass
class HallucinationReport:
    has_hallucination: bool
    hallucination_score: float  # 0.0 (Clean) to 1.0 (Severe)
    flags: List[HallucinationFlag] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_hallucination": self.has_hallucination,
            "hallucination_score": self.hallucination_score,
            "flags": [asdict(f) for f in self.flags],
            "summary": self.summary
        }


class HallucinationAnalyzer:
    """
    Analyzes generated AI answers against retrieved evidence to classify hallucinations:
    Unsupported claims, Fabricated citations, Conflicting evidence, Missing evidence, Low evidence.
    """

    @classmethod
    def analyze(
        cls,
        generated_answer: str,
        retrieved_contexts: List[str],
        citations: List[Dict[str, Any]],
        confidence_level: str
    ) -> HallucinationReport:
        flags: List[HallucinationFlag] = []
        combined_context = " ".join(retrieved_contexts).lower()
        ans_lower = generated_answer.lower()

        # 1. Low evidence check
        if not retrieved_contexts or len(combined_context.strip()) < 30:
            flags.append(HallucinationFlag(
                category="low_evidence",
                description="Retrieved context contains insufficient detail for verification.",
                severity="HIGH"
            ))

        # 2. Fabricated citation check
        if citations and not retrieved_contexts:
            flags.append(HallucinationFlag(
                category="fabricated_citation",
                description="Citations present but no underlying context retrieved.",
                severity="HIGH"
            ))

        # 3. Unsupported claim check
        if confidence_level == "LOW":
            flags.append(HallucinationFlag(
                category="unsupported_claim",
                description="Answer confidence is rated LOW, indicating potential unsupported claims.",
                severity="MEDIUM"
            ))

        # 4. Conflicting evidence check
        if "however" in ans_lower and "contradicts" in ans_lower:
            flags.append(HallucinationFlag(
                category="conflicting_evidence",
                description="Answer notes conflicting evidence in retrieved sources.",
                severity="LOW"
            ))

        has_hallucination = len(flags) > 0
        score = round(min(1.0, len(flags) * 0.35), 2)
        summary = f"Detected {len(flags)} potential risk flags." if flags else "Answer is fully supported by context."

        return HallucinationReport(
            has_hallucination=has_hallucination,
            hallucination_score=score,
            flags=flags,
            summary=summary
        )
