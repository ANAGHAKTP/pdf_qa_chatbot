import os
import uuid
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy import func
from app.ai.common import get_qdrant_client
from app.ai.ingestion.file_validation import FileValidator
from app.ai.ingestion.ocr import OCRProcessor
from app.ai.ingestion.structure import DocumentStructureAnalyzer
from app.ai.ingestion.tables import TableExtractor
from app.ai.ingestion.images import ImageExtractor
from app.ai.ingestion.metadata import MetadataEnricher
from app.ai.ingestion.chunker import AdvancedChunker

logger = logging.getLogger(__name__)


class ModularIngestionPipeline:
    """
    Multimodal Document Ingestion Pipeline connecting all 9 stages:
    Document -> File Validation -> Metadata Extraction -> OCR -> Layout Analysis -> Table Extraction -> Image Extraction -> Section Detection -> Chunk Generation -> Embedding -> Indexing
    """

    def __init__(self):
        self.validator = FileValidator()
        self.ocr_processor = OCRProcessor()
        self.analyzer = DocumentStructureAnalyzer()
        self.chunker = AdvancedChunker()

    def process_and_index(self, doc_id: int, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        # 0. Idempotent pre-cleanup of existing artifacts for this document
        from app.ai.pipeline import remove_document_embeddings
        remove_document_embeddings(doc_id)

        # 1. Validation
        val_res = self.validator.validate(filename, file_bytes)
        if not val_res.is_valid:
            raise ValueError(f"Validation error: {val_res.error_message}")

        # Extract PyPDFLoader pages
        import tempfile
        from langchain_community.document_loaders import PyPDFLoader

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            loader = PyPDFLoader(tmp_path)
            raw_pdf_pages = loader.load()
            pages_data = [{"page_num": idx + 1, "text": p.page_content} for idx, p in enumerate(raw_pdf_pages)]
        except Exception as e:
            text_str = file_bytes.decode("utf-8", errors="ignore")
            pages_data = [{"page_num": 1, "text": text_str}]
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # 3. OCR Stage
        ocr_results, is_scanned = self.ocr_processor.process_pages(pages_data)
        ocr_confidence = float(sum(r.ocr_confidence for r in ocr_results) / len(ocr_results)) if ocr_results else 1.0

        # Update pages_data with OCR text if applied
        for r in ocr_results:
            pages_data[r.page_num - 1]["text"] = r.text

        # 2. Save Parent pages to Database (DocumentPage table)
        from app.db.session import SessionLocal
        from app.db.models import Document, DocumentPage, DocumentChunk

        with SessionLocal() as db:
            for p in pages_data:
                db_page = DocumentPage(
                    doc_id=doc_id,
                    page_num=p["page_num"],
                    text=p["text"]
                )
                db.add(db_page)
            db.commit()

        # 4. Structure & Layout Analysis
        outline = self.analyzer.analyze_document(pages_data)

        # 5. Table Extraction
        extracted_tables = []
        for p in pages_data:
            tbls = TableExtractor.extract_from_text(p["page_num"], doc_id, p["text"])
            extracted_tables.extend(tbls)

        # 6. Image & Figure Extraction
        extracted_figures = []
        for p in pages_data:
            figs = ImageExtractor.extract_from_page(p["page_num"], doc_id, p["text"])
            extracted_figures.extend(figs)

        # 7. Metadata Enrichment
        sections_titles = [s["title"] for s in outline.sections]
        pages_text_list = [p["text"] for p in pages_data]
        doc_meta = MetadataEnricher.enrich(
            doc_id=doc_id,
            filename=filename,
            file_size=val_res.file_size,
            pages_text=pages_text_list,
            is_scanned=is_scanned,
            ocr_confidence=ocr_confidence,
            tables_count=len(extracted_tables),
            figures_count=len(extracted_figures),
            sections=sections_titles
        )

        # Update Document record with enriched metadata JSON in DB
        meta_dict = doc_meta.to_dict()
        with SessionLocal() as db:
            doc_record = db.query(Document).filter(Document.id == doc_id).first()
            if doc_record:
                doc_record.doc_metadata = meta_dict
                db.commit()

        # 8. Structure-Aware Advanced Chunking
        multimodal_chunks = self.chunker.chunk_document(
            doc_id=doc_id,
            structure_items=outline.structure_items,
            tables=extracted_tables,
            figures=extracted_figures
        )

        # 9. Index Chunks in Database (DocumentChunk + search_vector) and Qdrant
        if multimodal_chunks:
            texts = [c.content for c in multimodal_chunks]
            metadatas = [
                {
                    "doc_id": c.doc_id,
                    "page": c.page,
                    "chunk_idx": c.chunk_idx,
                    "chunk_id": c.chunk_id,
                    "chunk_type": c.chunk_type,
                    "parent_section": c.parent_section or "General",
                    **c.metadata
                }
                for c in multimodal_chunks
            ]

            # Deterministic UUIDv5 IDs for Qdrant points
            NAMESPACE_DOCMIND = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
            point_ids = [
                str(uuid.uuid5(NAMESPACE_DOCMIND, f"{c.doc_id}_{c.chunk_id}"))
                for c in multimodal_chunks
            ]

            # A. Save chunks to PostgreSQL DocumentChunk table
            with SessionLocal() as db:
                is_postgres = db.bind and db.bind.dialect.name == "postgresql"
                for c, meta in zip(multimodal_chunks, metadatas):
                    search_vec_val = func.to_tsvector('english', c.content) if is_postgres else c.content
                    chunk_obj = DocumentChunk(
                        doc_id=c.doc_id,
                        page=c.page,
                        chunk_idx=c.chunk_idx,
                        chunk_id=c.chunk_id,
                        content=c.content,
                        parent_section=c.parent_section or "General",
                        metadata_json=meta,
                        search_vector=search_vec_val
                    )
                    db.add(chunk_obj)
                db.commit()

            # B. Index in Qdrant Cloud
            try:
                vectorstore = get_qdrant_client()
                vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=point_ids)
            except Exception as qdrant_err:
                logger.error(f"Failed to index chunks into Qdrant: {qdrant_err}")
                raise qdrant_err

        logger.info(f"Ingested doc #{doc_id} ('{filename}'): {len(multimodal_chunks)} chunks, {len(extracted_tables)} tables, {len(extracted_figures)} figures.")

        return {
            "doc_id": doc_id,
            "chunk_count": len(multimodal_chunks),
            "metadata": meta_dict,
            "table_count": len(extracted_tables),
            "figure_count": len(extracted_figures)
        }
