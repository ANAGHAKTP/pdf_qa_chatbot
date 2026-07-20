import os
from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ValidationResult:
    is_valid: bool
    file_type: str  # "pdf", "image", "text", "unknown"
    file_size: int
    error_message: str = ""


class FileValidator:
    """
    Stage 1: File Validation
    Validates upload file integrity, MIME header, size constraints, and file extension.
    """

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".txt"}
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB limit

    @classmethod
    def validate(cls, filename: str, file_bytes: bytes) -> ValidationResult:
        if not file_bytes:
            return ValidationResult(is_valid=False, file_type="unknown", file_size=0, error_message="File is empty")

        size = len(file_bytes)
        if size > cls.MAX_FILE_SIZE_BYTES:
            return ValidationResult(is_valid=False, file_type="unknown", file_size=size, error_message="File size exceeds maximum 50MB limit")

        ext = os.path.splitext(filename.lower())[1]
        if ext not in cls.ALLOWED_EXTENSIONS:
            return ValidationResult(is_valid=False, file_type="unknown", file_size=size, error_message=f"Unsupported file format '{ext}'")

        if ext == ".pdf" or file_bytes.startswith(b"%PDF"):
            file_type = "pdf"
        elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"} or file_bytes[:4] in {b"\x89PNG", b"\xff\xd8\xff"}:
            file_type = "image"
        elif ext == ".txt":
            file_type = "text"
        else:
            file_type = "pdf" if ext == ".pdf" else "unknown"

        return ValidationResult(is_valid=True, file_type=file_type, file_size=size)
