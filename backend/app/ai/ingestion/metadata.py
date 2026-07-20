import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class DocumentMetadata:
    doc_id: int
    title: str
    author: Optional[str]
    creation_date: str
    language: str
    page_count: int
    file_size_bytes: int
    is_scanned: bool
    ocr_applied: bool
    ocr_confidence: float
    table_count: int
    figure_count: int
    document_category: str  # "Financial Report", "Legal Contract", "Technical Manual", "General Document"
    keywords: List[str] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetadataEnricher:
    """
    Stage 6: Metadata Enricher
    Enriches document metadata with language, category classification, keyword tags,
    page counts, and multimodal metrics for fine-grained retrieval filters.
    """

    CATEGORY_KEYWORDS = {
        "Financial Report": ["revenue", "quarter", "ebitda", "balance sheet", "fiscal", "profit", "audit", "tax", "income"],
        "Legal Contract": ["agreement", "party", "indemnify", "governing law", "termination", "liability", "clause", "signature"],
        "Technical Manual": ["specification", "installation", "architecture", "system", "api", "configuration", "hardware"],
    }

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Simple language detector fallback."""
        if not text:
            return "en"
        text_lower = text.lower()
        if re.search(r"\b(und|der|die|das|mit)\b", text_lower):
            return "de"
        if re.search(r"\b(les|pour|avec|dans)\b", text_lower):
            return "fr"
        if re.search(r"\b(los|las|por|para)\b", text_lower):
            return "es"
        return "en"

    @classmethod
    def classify_category(cls, text: str) -> str:
        """Classifies document type based on domain keyword frequencies."""
        text_lower = text.lower()
        category_scores = {}

        for category, kw_list in cls.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in kw_list if kw in text_lower)
            category_scores[category] = score

        best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        if category_scores[best_category] > 0:
            return best_category
        return "General Document"

    @classmethod
    def enrich(
        cls,
        doc_id: int,
        filename: str,
        file_size: int,
        pages_text: List[str],
        is_scanned: bool,
        ocr_confidence: float,
        tables_count: int,
        figures_count: int,
        sections: List[str]
    ) -> DocumentMetadata:
        full_text = " ".join(pages_text)
        page_count = len(pages_text)
        language = cls.detect_language(full_text[:2000])
        category = cls.classify_category(full_text[:5000])

        # Extract top keywords
        words = re.findall(r"\b[A-Za-z0-9_-]{4,}\b", full_text)
        from collections import Counter
        common_words = [w for w, _ in Counter(words).most_common(8) if w.lower() not in {"this", "that", "with", "from", "have"}]

        title = filename
        if pages_text and pages_text[0].strip():
            first_line = pages_text[0].strip().split("\n")[0]
            if len(first_line) < 80:
                title = first_line

        return DocumentMetadata(
            doc_id=doc_id,
            title=title,
            author="System Ingestion Engine",
            creation_date=datetime.utcnow().isoformat(),
            language=language,
            page_count=page_count,
            file_size_bytes=file_size,
            is_scanned=is_scanned,
            ocr_applied=is_scanned,
            ocr_confidence=ocr_confidence,
            table_count=tables_count,
            figure_count=figures_count,
            document_category=category,
            keywords=common_words,
            sections=sections
        )
