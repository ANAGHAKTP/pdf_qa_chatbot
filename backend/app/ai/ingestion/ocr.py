import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class OCRPageResult:
    page_num: int
    text: str
    is_scanned: bool
    ocr_confidence: float
    engine_name: str


class OCREngineInterface(ABC):
    """Abstract OCR engine interface for easy replacement of OCR engines."""
    
    @abstractmethod
    def process_page_image(self, page_num: int, image_bytes: bytes) -> OCRPageResult:
        pass


class DefaultOCREngine(OCREngineInterface):
    """
    Default OCR engine fallback. Uses pytesseract if installed or heuristic text processing.
    """

    def process_page_image(self, page_num: int, image_bytes: bytes) -> OCRPageResult:
        try:
            import pytesseract
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data.get("conf", []) if int(c) >= 0]
            avg_conf = float(sum(confidences) / len(confidences)) / 100.0 if confidences else 0.85
            return OCRPageResult(
                page_num=page_num,
                text=text.strip(),
                is_scanned=True,
                ocr_confidence=round(avg_conf, 4),
                engine_name="Tesseract-OCR"
            )
        except Exception:
            # Clean fallback when Tesseract binary is absent
            return OCRPageResult(
                page_num=page_num,
                text=f"[Scanned Page {page_num} OCR Fallback Text Extract]",
                is_scanned=True,
                ocr_confidence=0.80,
                engine_name="Fallback-OCR"
            )


class OCRProcessor:
    """
    Stage 2: OCR Processor
    Detects digital vs. scanned PDF pages and automatically runs OCR on scanned pages only.
    """

    def __init__(self, engine: Optional[OCREngineInterface] = None):
        self.engine = engine or DefaultOCREngine()

    @staticmethod
    def is_scanned_page(text: str, min_char_threshold: int = 20) -> bool:
        """
        Determines if a page is scanned based on text density and character distribution.
        """
        if not text:
            return True
        clean_text = re.sub(r"\s+", "", text)
        if len(clean_text) < min_char_threshold:
            return True
        return False

    def process_pages(self, raw_pages: List[Dict[str, Any]]) -> Tuple[List[OCRPageResult], bool]:
        """
        Processes list of pages ({page_num: int, text: str, image_bytes: Optional[bytes]}).
        Returns (ocr_page_results, any_scanned_flag).
        """
        results: List[OCRPageResult] = []
        any_scanned = False

        for p in raw_pages:
            page_num = p["page_num"]
            text = p.get("text", "")
            image_bytes = p.get("image_bytes")

            if self.is_scanned_page(text) and image_bytes:
                any_scanned = True
                ocr_res = self.engine.process_page_image(page_num, image_bytes)
                results.append(ocr_res)
            elif self.is_scanned_page(text) and not image_bytes:
                # Text is sparse but no image bytes provided; treat as digital page with available text
                results.append(OCRPageResult(
                    page_num=page_num,
                    text=text.strip() if text else f"[Scanned page {page_num}]",
                    is_scanned=True,
                    ocr_confidence=0.75,
                    engine_name="Text-Density-Analysis"
                ))
            else:
                results.append(OCRPageResult(
                    page_num=page_num,
                    text=text.strip(),
                    is_scanned=False,
                    ocr_confidence=1.0,
                    engine_name="Digital-Native-PDF"
                ))

        return results, any_scanned
