import os
import pickle
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from app.ai.common import load_parent_content

@dataclass
class ContextChunk:
    text: str
    doc_id: int
    page: int
    chunk_idx: int
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_text: Optional[str] = None


@dataclass
class ContextResult:
    chunks: List[ContextChunk]
    formatted_context: str
    total_tokens_approx: int
    merged_count: int
    deduped_count: int


class ContextBuilder:
    """
    ContextBuilder component responsible for:
    - Removing duplicate chunks
    - Merging nearby chunks (e.g., adjacent chunks on the same page)
    - Preserving document ordering
    - Enforcing token budget
    - Preserving metadata
    """

    def __init__(self, max_token_budget: int = 3000):
        self.max_token_budget = max_token_budget

    @staticmethod
    def deduplicate_chunks(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """Removes duplicate text or identical metadata chunk IDs."""
        unique_chunks = []
        seen_keys = set()
        seen_texts = set()
        deduped_count = 0

        for chunk in chunks:
            m = chunk.get("metadata", {})
            doc_id = m.get("doc_id")
            page = m.get("page")
            chunk_idx = m.get("chunk_idx")
            key = f"{doc_id}_{page}_{chunk_idx}" if doc_id and page is not None and chunk_idx is not None else None
            
            content_snippet = chunk["content"].strip().lower()[:100]

            if (key and key in seen_keys) or (content_snippet in seen_texts):
                deduped_count += 1
                continue

            if key:
                seen_keys.add(key)
            seen_texts.add(content_snippet)
            unique_chunks.append(chunk)

        return unique_chunks, deduped_count

    @staticmethod
    def merge_nearby_chunks(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Merges chunks that belong to the same doc and page if they are adjacent or sequential.
        """
        if not chunks:
            return [], 0

        # Group by (doc_id, page)
        merged = []
        merged_count = 0
        
        # Sort chunks by doc_id, page, chunk_idx first to find adjacencies
        sorted_chunks = sorted(
            chunks,
            key=lambda c: (
                c.get("metadata", {}).get("doc_id", 0),
                c.get("metadata", {}).get("page", 0),
                c.get("metadata", {}).get("chunk_idx", 0)
            )
        )

        curr = None

        for c in sorted_chunks:
            if curr is None:
                curr = dict(c)
                continue

            c_meta = c.get("metadata", {})
            curr_meta = curr.get("metadata", {})

            same_doc = c_meta.get("doc_id") == curr_meta.get("doc_id")
            same_page = c_meta.get("page") == curr_meta.get("page")
            is_adjacent = abs(c_meta.get("chunk_idx", 0) - curr_meta.get("chunk_idx", 0)) <= 1

            if same_doc and same_page and is_adjacent:
                # Merge texts
                if c["content"].strip() not in curr["content"]:
                    curr["content"] = curr["content"].strip() + "\n" + c["content"].strip()
                    # Max score preserved
                    curr["score"] = max(curr.get("score", 0), c.get("score", 0))
                    merged_count += 1
            else:
                merged.append(curr)
                curr = dict(c)

        if curr is not None:
            merged.append(curr)

        return merged, merged_count

    def build_context(
        self,
        chunks: List[Dict[str, Any]],
        doc_map: Optional[Dict[int, str]] = None
    ) -> ContextResult:
        if not chunks:
            return ContextResult(chunks=[], formatted_context="", total_tokens_approx=0, merged_count=0, deduped_count=0)

        # 1. Deduplicate
        deduped, deduped_count = self.deduplicate_chunks(chunks)

        # 2. Merge nearby chunks
        merged_chunks, merged_count = self.merge_nearby_chunks(deduped)

        # 3. Preserve document ordering (sort by doc_id, page, chunk_idx)
        ordered_chunks = sorted(
            merged_chunks,
            key=lambda c: (
                c.get("metadata", {}).get("doc_id", 0),
                c.get("metadata", {}).get("page", 0),
                c.get("metadata", {}).get("chunk_idx", 0)
            )
        )

        # 4. Convert to ContextChunk objects and enforce token budget
        context_chunks: List[ContextChunk] = []
        formatted_blocks = []
        current_token_count = 0

        # Approx 1 token = ~4 chars
        char_budget = self.max_token_budget * 4

        for idx, chunk in enumerate(ordered_chunks):
            m = chunk.get("metadata", {})
            doc_id = m.get("doc_id", 0)
            page_num = m.get("page", 1)
            chunk_idx = m.get("chunk_idx", 0)
            score = chunk.get("score", 0.5)
            content = chunk["content"]

            parent_text = load_parent_content(doc_id, page_num)
            effective_text = parent_text if parent_text else content

            # Estimate length
            text_len = len(effective_text)
            if current_token_count + (text_len // 4) > self.max_token_budget and context_chunks:
                # Truncate text if partial room remains, or stop
                remaining_chars = char_budget - (current_token_count * 4)
                if remaining_chars > 200:
                    effective_text = effective_text[:remaining_chars] + "... [truncated]"
                else:
                    break

            current_token_count += len(effective_text) // 4

            doc_name = doc_map.get(doc_id, f"Document #{doc_id}") if doc_map else f"Document #{doc_id}"

            c_obj = ContextChunk(
                text=effective_text,
                doc_id=doc_id,
                page=page_num,
                chunk_idx=chunk_idx,
                score=score,
                metadata=m,
                parent_text=parent_text
            )
            context_chunks.append(c_obj)

            formatted_blocks.append(
                f"[Source {len(context_chunks)}]: {doc_name} (Page {page_num})\n{effective_text}"
            )

        formatted_context = "\n\n".join(formatted_blocks)

        return ContextResult(
            chunks=context_chunks,
            formatted_context=formatted_context,
            total_tokens_approx=current_token_count,
            merged_count=merged_count,
            deduped_count=deduped_count
        )
