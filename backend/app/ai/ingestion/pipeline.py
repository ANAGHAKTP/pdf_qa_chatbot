import os
import pickle
import logging
from typing import List, Dict, Any, Tuple
from app.ai.common import get_chroma_client, PARENTS_DIR, BM25_DIR
from app.ai.ingestion.file_validation import FileValidator
from app.ai.ingestion.ocr import OCRProcessor
from app.ai.ingestion.structure import DocumentStructureAnalyzer
from app.ai.ingestion.tables import TableExtractor
from app.ai.ingestion.images import ImageExtractor
from app.ai.ingestion.metadata import MetadataEnricher
from app.ai.ingestion.chunker import AdvancedChunker
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

METADATA_DIR = "./data/metadata"
os.makedirs(METADATA_DIR, exist_ok=True)


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

        # 2. Save Parent pages to disk
        doc_parents = {str(p["page_num"]): p["text"] for p in pages_data}
        with open(os.path.join(PARENTS_DIR, f"{doc_id}.pkl"), "wb") as f:
            pickle.dump(doc_parents, f)

        # 3. OCR Stage
        ocr_results, is_scanned = self.ocr_processor.process_pages(pages_data)
        ocr_confidence = float(sum(r.ocr_confidence for r in ocr_results) / len(ocr_results)) if ocr_results else 1.0

        # Update pages_data with OCR text if applied
        for r in ocr_results:
            pages_data[r.page_num - 1]["text"] = r.text

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

        # Save metadata JSON to disk
        import json
        with open(os.path.join(METADATA_DIR, f"{doc_id}.json"), "w") as f:
            json.dump(doc_meta.to_dict(), f, indent=2)

        # 8. Structure-Aware Advanced Chunking
        multimodal_chunks = self.chunker.chunk_document(
            doc_id=doc_id,
            structure_items=outline.structure_items,
            tables=extracted_tables,
            figures=extracted_figures
        )

        # 9. Index Chunks in ChromaDB and BM25
        if multimodal_chunks:
            vectorstore = get_chroma_client()
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
            ids = [c.chunk_id for c in multimodal_chunks]
            vectorstore.add_texts(texts=texts, metadatas=metadatas, ids=ids)

            # Build BM25
            tokenized_corpus = [t.lower().split() for t in texts]
            bm25 = BM25Okapi(tokenized_corpus)
            bm25_data = {
                "bm25": bm25,
                "texts": texts,
                "metadatas": metadatas
            }
            with open(os.path.join(BM25_DIR, f"{doc_id}.pkl"), "wb") as f:
                pickle.dump(bm25_data, f)

        logger.info(f"Ingested doc #{doc_id} ('{filename}'): {len(multimodal_chunks)} chunks, {len(extracted_tables)} tables, {len(extracted_figures)} figures.")

        return {
            "doc_id": doc_id,
            "chunk_count": len(multimodal_chunks),
            "metadata": doc_meta.to_dict(),
            "table_count": len(extracted_tables),
            "figure_count": len(extracted_figures)
        }
