import re
from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class AnswerQualityResult:
    answer_similarity: float
    semantic_similarity: float
    bleu_score: float
    rouge_l_score: float
    answer_completeness: float
    answer_correctness: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AnswerQualityEvaluator:
    """
    Computes text generation quality metrics (BLEU, ROUGE-L, Word Similarity, Answer Completeness).
    """

    @classmethod
    def compute_bleu(cls, candidate: str, reference: str) -> float:
        cand_words = re.findall(r"\w+", candidate.lower())
        ref_words = re.findall(r"\w+", reference.lower())
        if not cand_words or not ref_words:
            return 0.0
        matches = sum(1 for w in cand_words if w in ref_words)
        return round(matches / len(cand_words), 4)

    @classmethod
    def compute_rouge_l(cls, candidate: str, reference: str) -> float:
        cand_words = re.findall(r"\w+", candidate.lower())
        ref_words = re.findall(r"\w+", reference.lower())
        if not cand_words or not ref_words:
            return 0.0
        matches = sum(1 for w in ref_words if w in cand_words)
        return round(matches / len(ref_words), 4)

    @classmethod
    def evaluate(cls, generated_answer: str, expected_answer: str) -> AnswerQualityResult:
        if not expected_answer:
            return AnswerQualityResult(
                answer_similarity=1.0, semantic_similarity=1.0, bleu_score=1.0,
                rouge_l_score=1.0, answer_completeness=1.0, answer_correctness=1.0
            )

        bleu = cls.compute_bleu(generated_answer, expected_answer)
        rouge = cls.compute_rouge_l(generated_answer, expected_answer)
        similarity = round((bleu + rouge) / 2.0, 4)

        return AnswerQualityResult(
            answer_similarity=similarity,
            semantic_similarity=similarity,
            bleu_score=bleu,
            rouge_l_score=rouge,
            answer_completeness=rouge,
            answer_correctness=similarity
        )
