import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class ExtractedTable:
    table_id: str
    page_num: int
    headers: List[str]
    rows: List[List[str]]
    markdown_content: str
    caption: Optional[str] = None
    row_count: int = 0
    column_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TableExtractor:
    """
    Stage 4: Table Extractor
    Detects tabular structures in PDF content, converts them to Markdown tables,
    and indexes them with table metadata.
    """

    TABLE_GRID_PATTERN = r"\|.*?\|"

    @classmethod
    def extract_from_text(cls, page_num: int, doc_id: int, text: str) -> List[ExtractedTable]:
        tables: List[ExtractedTable] = []
        lines = text.split("\n")
        table_buffer: List[str] = []
        table_idx = 1

        def flush_table():
            nonlocal table_idx, table_buffer
            if len(table_buffer) >= 2:
                # Parse markdown table lines
                rows_data = []
                for line in table_buffer:
                    cells = [c.strip() for c in line.split("|")[1:-1]]
                    if cells and not all(c.startswith("---") or c.startswith(":-") for c in cells):
                        rows_data.append(cells)

                if rows_data:
                    headers = rows_data[0]
                    data_rows = rows_data[1:] if len(rows_data) > 1 else []
                    md = "\n".join(table_buffer)

                    tbl = ExtractedTable(
                        table_id=f"table_{doc_id}_{page_num}_{table_idx}",
                        page_num=page_num,
                        headers=headers,
                        rows=data_rows,
                        markdown_content=md,
                        caption=f"Table {table_idx} on Page {page_num}",
                        row_count=len(rows_data),
                        column_count=len(headers)
                    )
                    tables.append(tbl)
                    table_idx += 1
            table_buffer = []

        for line in lines:
            line_str = line.strip()
            if line_str.startswith("|") and line_str.endswith("|"):
                table_buffer.append(line_str)
            else:
                if table_buffer:
                    flush_table()

        if table_buffer:
            flush_table()

        return tables
