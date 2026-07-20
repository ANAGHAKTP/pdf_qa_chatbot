import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from app.ai.ingestion.structure import StructureItem
from app.ai.ingestion.tables import ExtractedTable
from app.ai.ingestion.images import ExtractedImage

@dataclass
class MultimodalChunk:
    chunk_id: str
    doc_id: int
    page: int
    chunk_idx: int
    chunk_type: str  # "text", "table", "figure", "code"
    content: str
    parent_section: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdvancedChunker:
    """
    Stage 7: Structure-Aware Advanced Chunker
    Ensures tables, headings, figure captions, and code blocks are NEVER split across chunk boundaries.
    """

    def __init__(self, target_chunk_size: int = 400, overlap: int = 80):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def chunk_document(
        self,
        doc_id: int,
        structure_items: List[StructureItem],
        tables: List[ExtractedTable],
        figures: List[ExtractedImage]
    ) -> List[MultimodalChunk]:
        chunks: List[MultimodalChunk] = []

        # 1. Index Tables as unbroken single chunks
        for tbl in tables:
            chunk_id = f"{doc_id}_p{tbl.page_num}_tbl_{tbl.table_id}"
            chunks.append(MultimodalChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                page=tbl.page_num,
                chunk_idx=len(chunks),
                chunk_type="table",
                content=f"[TABLE: {tbl.caption}]\n{tbl.markdown_content}",
                parent_section=f"Page {tbl.page_num} Tables",
                metadata={
                    "table_id": tbl.table_id,
                    "row_count": tbl.row_count,
                    "col_count": tbl.column_count,
                    "is_table": True
                }
            ))

        # 2. Index Figures as unbroken single chunks
        for fig in figures:
            chunk_id = f"{doc_id}_p{fig.page_num}_fig_{fig.figure_id}"
            chunks.append(MultimodalChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                page=fig.page_num,
                chunk_idx=len(chunks),
                chunk_type="figure",
                content=f"[FIGURE: {fig.caption}]\nContext: {fig.surrounding_text}",
                parent_section=f"Page {fig.page_num} Figures",
                metadata={
                    "figure_id": fig.figure_id,
                    "figure_type": fig.figure_type,
                    "is_figure": True
                }
            ))

        # 3. Chunk text structure items while preserving headings and paragraph integrity
        text_buffer = ""
        current_page = 1
        current_section = "General"

        for item in structure_items:
            content_str = item.content.strip()
            if not content_str:
                continue

            # Heading starts a new semantic section
            if item.item_type in {"heading_1", "heading_2", "heading_3"}:
                if text_buffer:
                    chunk_id = f"{doc_id}_p{current_page}_text_{len(chunks)}"
                    chunks.append(MultimodalChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        page=current_page,
                        chunk_idx=len(chunks),
                        chunk_type="text",
                        content=text_buffer.strip(),
                        parent_section=current_section,
                        metadata={"section": current_section}
                    ))
                    text_buffer = ""

                current_section = content_str
                current_page = item.page_num
                text_buffer = f"## {content_str}\n"
                continue

            current_page = item.page_num
            # Check length constraint
            if len(text_buffer) + len(content_str) > self.target_chunk_size:
                if text_buffer:
                    chunk_id = f"{doc_id}_p{current_page}_text_{len(chunks)}"
                    chunks.append(MultimodalChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        page=current_page,
                        chunk_idx=len(chunks),
                        chunk_type="text",
                        content=text_buffer.strip(),
                        parent_section=current_section,
                        metadata={"section": current_section}
                    ))
                text_buffer = content_str + "\n"
            else:
                text_buffer += content_str + "\n"

        if text_buffer.strip():
            chunk_id = f"{doc_id}_p{current_page}_text_{len(chunks)}"
            chunks.append(MultimodalChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                page=current_page,
                chunk_idx=len(chunks),
                chunk_type="text",
                content=text_buffer.strip(),
                parent_section=current_section,
                metadata={"section": current_section}
            ))

        return chunks
