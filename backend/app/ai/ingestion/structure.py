import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict

@dataclass
class StructureItem:
    item_type: str  # "title", "heading_1", "heading_2", "heading_3", "paragraph", "list_item", "code_block"
    content: str
    page_num: int
    section_title: Optional[str] = None
    level: int = 1


@dataclass
class DocumentOutline:
    title: str
    sections: List[Dict[str, Any]] = field(default_factory=list)
    total_headings: int = 0
    structure_items: List[StructureItem] = field(default_factory=list)


class DocumentStructureAnalyzer:
    """
    Stage 3: Layout & Structure Analysis
    Detects titles, section headings, lists, paragraphs, and document hierarchy.
    """

    HEADING_PATTERNS = [
        (r"^(?:#\s+)(.+)$", "heading_1", 1),
        (r"^(?:##\s+)(.+)$", "heading_2", 2),
        (r"^(?:###\s+)(.+)$", "heading_3", 3),
        (r"^(?:[0-9]+\.[0-9]*\s+)([A-Z0-9\s_-]{3,60})$", "heading_2", 2),
        (r"^([A-Z0-9\s_-]{4,60})$", "heading_2", 2),
    ]

    LIST_PATTERN = r"^(?:[-*•]\s+|\d+\.\s+)"

    @classmethod
    def analyze_page(cls, page_num: int, text: str, current_section: Optional[str] = None) -> Tuple[List[StructureItem], Optional[str]]:
        items: List[StructureItem] = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        active_section = current_section

        for line in lines:
            # Check list item
            if re.match(cls.LIST_PATTERN, line):
                items.append(StructureItem(
                    item_type="list_item",
                    content=line,
                    page_num=page_num,
                    section_title=active_section,
                    level=3
                ))
                continue

            # Check heading pattern
            is_heading = False
            for pattern, item_type, level in cls.HEADING_PATTERNS:
                m = re.match(pattern, line)
                if m:
                    heading_text = m.group(1).strip()
                    active_section = heading_text
                    items.append(StructureItem(
                        item_type=item_type,
                        content=heading_text,
                        page_num=page_num,
                        section_title=heading_text,
                        level=level
                    ))
                    is_heading = True
                    break

            if not is_heading:
                items.append(StructureItem(
                    item_type="paragraph",
                    content=line,
                    page_num=page_num,
                    section_title=active_section,
                    level=4
                ))

        return items, active_section

    @classmethod
    def analyze_document(cls, pages: List[Dict[str, Any]]) -> DocumentOutline:
        all_items: List[StructureItem] = []
        sections = []
        current_section = "General Overview"
        doc_title = "Untitled Document"

        for p in pages:
            page_num = p["page_num"]
            text = p.get("text", "")
            items, current_section = cls.analyze_page(page_num, text, current_section)

            for item in items:
                all_items.append(item)
                if item.item_type in {"heading_1", "heading_2"}:
                    sections.append({
                        "title": item.content,
                        "page": page_num,
                        "level": item.level
                    })
                    if doc_title == "Untitled Document" and item.level == 1:
                        doc_title = item.content

        if doc_title == "Untitled Document" and all_items:
            doc_title = all_items[0].content[:60]

        return DocumentOutline(
            title=doc_title,
            sections=sections,
            total_headings=len(sections),
            structure_items=all_items
        )
