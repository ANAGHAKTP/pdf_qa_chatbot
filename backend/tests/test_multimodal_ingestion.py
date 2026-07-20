import os
import pytest
from app.ai.ingestion.file_validation import FileValidator
from app.ai.ingestion.ocr import OCRProcessor, DefaultOCREngine
from app.ai.ingestion.structure import DocumentStructureAnalyzer
from app.ai.ingestion.tables import TableExtractor
from app.ai.ingestion.images import ImageExtractor
from app.ai.ingestion.metadata import MetadataEnricher
from app.ai.ingestion.chunker import AdvancedChunker
from app.ai.ingestion.pipeline import ModularIngestionPipeline


def test_file_validator():
    val_res = FileValidator.validate("report.pdf", b"%PDF-1.4 sample content")
    assert val_res.is_valid is True
    assert val_res.file_type == "pdf"

    invalid_res = FileValidator.validate("exe_file.exe", b"binary content")
    assert invalid_res.is_valid is False


def test_ocr_processor():
    processor = OCRProcessor()
    
    # High density text -> Digital page
    assert processor.is_scanned_page("This is a clean high density text page with ample textual characters.", min_char_threshold=20) is False
    
    # Low density text -> Scanned page
    assert processor.is_scanned_page("Sparse text", min_char_threshold=50) is True

    pages = [{"page_num": 1, "text": "Digital native text content for page 1"}]
    ocr_results, any_scanned = processor.process_pages(pages)
    
    assert any_scanned is False
    assert len(ocr_results) == 1
    assert ocr_results[0].ocr_confidence == 1.0


def test_structure_analyzer():
    text_content = """
# Executive Summary
This document outlines Q3 financial performance.

## Financial Performance Tables
| Quarter | Revenue | EBITDA |
| Q1 | $10M | $2M |
| Q2 | $12M | $3M |

* Item 1: High growth
* Item 2: Cost reduction
"""

    outline = DocumentStructureAnalyzer.analyze_document([{"page_num": 1, "text": text_content}])

    assert outline.title == "Executive Summary"
    assert outline.total_headings >= 2
    assert len(outline.structure_items) > 0


def test_table_extractor():
    text_with_table = """
Some introductory text.

| Qtr | Revenue | Profit |
|---|---|---|
| Q1 | $100K | $20K |
| Q2 | $150K | $35K |

Concluding remark.
"""
    tables = TableExtractor.extract_from_text(page_num=1, doc_id=101, text=text_with_table)

    assert len(tables) == 1
    tbl = tables[0]
    assert tbl.page_num == 1
    assert tbl.column_count == 3
    assert tbl.row_count >= 2
    assert "Revenue" in tbl.headers


def test_image_extractor():
    text_with_fig = """
Figure 1: Quarterly Sales Revenue Growth Chart
As seen in Figure 1, sales expanded rapidly in Q3.
"""
    figures = ImageExtractor.extract_from_page(page_num=2, doc_id=101, text=text_with_fig)

    assert len(figures) == 1
    fig = figures[0]
    assert fig.page_num == 2
    assert "Figure 1" in fig.caption


def test_metadata_enricher():
    pages_text = [
        "Executive Q3 Financial Report Revenue EBITDA Profit Tax Agreement",
        "Detailed income statement party indemnification clause"
    ]
    sections = ["Executive Summary", "Financial Statement"]

    metadata = MetadataEnricher.enrich(
        doc_id=50,
        filename="Q3_Report.pdf",
        file_size=1024,
        pages_text=pages_text,
        is_scanned=False,
        ocr_confidence=1.0,
        tables_count=2,
        figures_count=1,
        sections=sections
    )

    assert metadata.doc_id == 50
    assert metadata.language == "en"
    assert metadata.document_category in {"Financial Report", "Legal Contract"}
    assert metadata.table_count == 2
    assert metadata.figure_count == 1
    assert len(metadata.keywords) > 0


def test_advanced_chunker_unbroken_tables_and_figures():
    outline = DocumentStructureAnalyzer.analyze_document([{"page_num": 1, "text": "# Section Header\nParagraph text body."}])
    tables = TableExtractor.extract_from_text(page_num=1, doc_id=1, text="| A | B |\n| 1 | 2 |")
    figures = ImageExtractor.extract_from_page(page_num=1, doc_id=1, text="Figure 1: Overview Diagram")

    chunker = AdvancedChunker()
    chunks = chunker.chunk_document(doc_id=1, structure_items=outline.structure_items, tables=tables, figures=figures)

    assert len(chunks) >= 3
    chunk_types = set(c.chunk_type for c in chunks)
    assert "table" in chunk_types
    assert "figure" in chunk_types
    assert "text" in chunk_types


def test_modular_ingestion_pipeline():
    pipeline = ModularIngestionPipeline()
    res = pipeline.process_and_index(
        doc_id=999,
        filename="test_multimodal.pdf",
        file_bytes=b"%PDF-1.4 Mock PDF content for multimodal testing\n# Title Header\n| Col1 | Col2 |\n| Val1 | Val2 |\nFigure 1: Test Figure"
    )

    assert res["doc_id"] == 999
    assert res["chunk_count"] >= 1
    assert "metadata" in res
