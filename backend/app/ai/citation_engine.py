import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from app.ai.context_builder import ContextChunk

@dataclass
class CitationItem:
    citation_num: int
    doc_id: int
    filename: str
    page: int
    chunk_idx: int
    chunk_id: str
    score: float
    highlighted_paragraph: str
    preview_url: Optional[str] = None
    page_offset: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CitationEngine:
    """
    CitationEngine module responsible for producing rich, accurate citations
    from context chunks and attaching confidence scores & document metadata.
    """

    @staticmethod
    def normalize_score(score: Optional[float]) -> float:
        """Converts cross-encoder logit or raw score to 0.0-1.0 confidence score."""
        if score is None:
            return 0.80
        # If score is already between 0 and 1
        if 0.0 <= score <= 1.0:
            return round(float(score), 4)
        # Sigmoid transform for logits
        sigmoid = 1.0 / (1.0 + np.exp(-score))
        return round(float(sigmoid), 4)

    @classmethod
    def generate_citations(
        cls,
        context_chunks: List[ContextChunk],
        doc_map: Optional[Dict[int, str]] = None
    ) -> List[CitationItem]:
        citations: List[CitationItem] = []

        for idx, chunk in enumerate(context_chunks):
            doc_id = chunk.doc_id
            page = chunk.page
            chunk_idx = chunk.chunk_idx
            filename = doc_map.get(doc_id, f"Document #{doc_id}") if doc_map else f"Document #{doc_id}"

            chunk_id = f"{doc_id}_{page}_{chunk_idx}"
            norm_score = cls.normalize_score(chunk.score)

            # Excerpt snippet
            excerpt = chunk.text
            if len(excerpt) > 300:
                excerpt = excerpt[:300].strip() + "..."

            cit = CitationItem(
                citation_num=idx + 1,
                doc_id=doc_id,
                filename=filename,
                page=page,
                chunk_idx=chunk_idx,
                chunk_id=chunk_id,
                score=norm_score,
                highlighted_paragraph=excerpt,
                preview_url=f"/api/v1/documents/{doc_id}/preview?page={page}",
                page_offset=page
            )
            citations.append(cit)

        return citations
