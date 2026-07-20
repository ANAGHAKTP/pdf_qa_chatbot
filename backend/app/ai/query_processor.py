import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from app.core.config import settings

@dataclass
class ProcessedQuery:
    raw_query: str
    normalized_query: str
    keywords: List[str] = field(default_factory=list)
    expanded_queries: List[str] = field(default_factory=list)
    metadata_filters: Dict[str, Any] = field(default_factory=dict)


class QueryProcessor:
    """
    Dedicated Query Processing module responsible for:
    - Query normalization
    - Keyword extraction
    - Metadata extraction (page ranges, dates, etc.)
    - Multi-query expansion
    """

    @staticmethod
    def normalize(query: str) -> str:
        """Normalizes query text by cleaning whitespace and casing."""
        if not query:
            return ""
        # Remove extra whitespace and special control chars
        text = re.sub(r"\s+", " ", query.strip())
        return text

    @staticmethod
    def extract_keywords(query: str) -> List[str]:
        """Extracts key terms and noun phrases from the query."""
        normalized = QueryProcessor.normalize(query)
        if not normalized:
            return []

        # Common stop words to exclude
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
            "in", "on", "at", "to", "for", "from", "by", "with", "about", "against",
            "between", "into", "through", "during", "before", "after", "above", "below",
            "what", "which", "who", "whom", "this", "that", "these", "those", "am",
            "how", "why", "where", "when", "can", "could", "would", "should", "does",
            "do", "did", "have", "has", "had", "of", "and", "or", "but", "if", "then"
        }

        # Tokenize and filter
        words = re.findall(r"\b[A-Za-z0-9_-]+\b", normalized)
        keywords = [w for w in words if w.lower() not in stop_words and len(w) > 1]
        
        # Deduplicate preserving order
        unique_keywords = []
        seen = set()
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)
        return unique_keywords

    @staticmethod
    def extract_metadata_filters(query: str) -> Dict[str, Any]:
        """
        Extracts structural metadata queries from prompt text.
        For example: 'on page 5', 'in page 12'.
        """
        filters: Dict[str, Any] = {}
        
        # Match 'page X' or 'pages X-Y'
        page_match = re.search(r"\bpage\s+(\d+)\b", query, re.IGNORECASE)
        if page_match:
            filters["page"] = int(page_match.group(1))

        return filters

    @staticmethod
    def expand_query(query: str) -> List[str]:
        """
        Generates multi-query expansion variations.
        Falls back to rule-based keyword variants if LLM API is unavailable.
        """
        normalized = QueryProcessor.normalize(query)
        queries = [normalized]
        if not normalized:
            return queries

        if settings.NVIDIA_API_KEY and "your-actual" not in settings.NVIDIA_API_KEY:
            try:
                from langchain_nvidia_ai_endpoints import ChatNVIDIA
                llm = ChatNVIDIA(
                    model=settings.LLM_MODEL,
                    api_key=settings.NVIDIA_API_KEY,
                    temperature=0.2
                )
                prompt = (
                    f"You are an information retrieval assistant. Generate exactly 3 alternative search queries "
                    f"for the user prompt: '{normalized}'.\n"
                    f"Provide only the alternative queries, one per line. Do not number them."
                )
                response = llm.invoke(prompt)
                alternatives = [line.strip() for line in str(response.content).split("\n") if line.strip()]
                clean_alternatives = []
                for alt in alternatives:
                    clean = alt.lstrip("0123456789.-*• ")
                    if clean and clean.lower() != normalized.lower():
                        clean_alternatives.append(clean)
                queries.extend(clean_alternatives[:3])
            except Exception as e:
                pass

        # Rule-based keyword expansion fallback if no LLM variants produced
        if len(queries) == 1:
            keywords = QueryProcessor.extract_keywords(normalized)
            if keywords:
                queries.append(" ".join(keywords))

        # Deduplicate
        seen = set()
        unique_queries = []
        for q in queries:
            q_clean = q.strip()
            if q_clean and q_clean.lower() not in seen:
                seen.add(q_clean.lower())
                unique_queries.append(q_clean)

        return unique_queries

    @classmethod
    def process(cls, query: str) -> ProcessedQuery:
        """Main entry point to parse and structure an incoming user query."""
        normalized = cls.normalize(query)
        keywords = cls.extract_keywords(normalized)
        metadata_filters = cls.extract_metadata_filters(normalized)
        expanded_queries = cls.expand_query(normalized)

        return ProcessedQuery(
            raw_query=query,
            normalized_query=normalized,
            keywords=keywords,
            expanded_queries=expanded_queries,
            metadata_filters=metadata_filters
        )
