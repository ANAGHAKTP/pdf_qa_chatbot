import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class ExtractedImage:
    figure_id: str
    page_num: int
    caption: str
    surrounding_text: str
    location_box: Dict[str, float]  # e.g., {"x0": 0, "y0": 0, "x1": 100, "y1": 100}
    image_url: Optional[str] = None
    figure_type: str = "figure"  # "figure", "chart", "diagram", "screenshot"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ImageExtractor:
    """
    Stage 5: Image & Figure Extractor
    Extracts visual figures, diagrams, charts, captions, and context.
    """

    FIGURE_CAPTION_PATTERN = r"(?m)^\s*(?:Figure|Fig\.|Chart|Diagram|Illustration)\s+\d+[:.]?\s*.*$"

    @classmethod
    def extract_from_page(
        cls,
        page_num: int,
        doc_id: int,
        text: str,
        image_metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[ExtractedImage]:
        extracted: List[ExtractedImage] = []
        fig_count = 1

        # 1. Parse captions from page text
        captions = list(set(re.findall(cls.FIGURE_CAPTION_PATTERN, text, re.IGNORECASE)))

        for cap in captions:
            fig_id = f"fig_{doc_id}_{page_num}_{fig_count}"
            caption_text = cap.strip()

            # Determine figure type
            fig_type = "chart" if "chart" in caption_text.lower() else ("diagram" if "diagram" in caption_text.lower() else "figure")

            extracted.append(ExtractedImage(
                figure_id=fig_id,
                page_num=page_num,
                caption=f"Figure {fig_count}: {caption_text}",
                surrounding_text=text[:300].strip(),
                location_box={"x0": 50.0, "y0": 100.0, "x1": 550.0, "y1": 400.0},
                image_url=f"/api/v1/documents/{doc_id}/figures/{fig_id}",
                figure_type=fig_type
            ))
            fig_count += 1

        # 2. If raw image metadata objects exist, register them
        if image_metadata_list:
            for img in image_metadata_list:
                fig_id = f"img_{doc_id}_{page_num}_{fig_count}"
                extracted.append(ExtractedImage(
                    figure_id=fig_id,
                    page_num=page_num,
                    caption=img.get("caption", f"Extracted Figure on Page {page_num}"),
                    surrounding_text=text[:200].strip(),
                    location_box=img.get("box", {"x0": 0.0, "y0": 0.0, "x1": 100.0, "y1": 100.0}),
                    image_url=f"/api/v1/documents/{doc_id}/figures/{fig_id}",
                    figure_type="figure"
                ))
                fig_count += 1

        return extracted
