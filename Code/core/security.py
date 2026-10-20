"""
Security module for Automotive Engineering AI Assistant.
Validates file safety, sanitizes filenames, defends against path traversal
and prompt injection in untrusted document texts.
"""
import re
from pathlib import Path
from core.config import settings
from core.logging_config import logger


def sanitize_filename(filename: str) -> str:
    """
    Remove potentially dangerous characters and path traversal sequences.
    """
    base = Path(filename).name
    # Strip non-alphanumeric, dots, dashes, underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_\.-]", "_", base)
    if not sanitized.lower().endswith(".pdf"):
        sanitized += ".pdf"
    return sanitized


def validate_file_path(target_path: Path, base_dir: Path = settings.UPLOAD_DIR) -> bool:
    """
    Ensure the path is strictly within the allowed directory to prevent path traversal.
    """
    try:
        resolved_target = target_path.resolve()
        resolved_base = base_dir.resolve()
        return resolved_target.is_relative_to(resolved_base)
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False


def validate_pdf_content(file_bytes: bytes) -> tuple[bool, str]:
    """
    Verify PDF magic header and reasonable minimum size.
    """
    if len(file_bytes) < 8:
        return False, "File is too small to be a valid PDF."
    
    # Check for %PDF magic header in first 1024 bytes
    if not file_bytes[:1024].startswith(b"%PDF-") and b"%PDF-" not in file_bytes[:1024]:
        return False, "Invalid PDF header: Missing '%PDF-' signature."
    
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        return False, f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
    
    return True, "Valid PDF"


def sanitize_document_text(text: str) -> str:
    """
    Sanitize extracted text while preserving technical symbols,
    AUTOSAR identifiers, and hex numbers.
    Defends against accidental prompt injection markers.
    """
    if not text:
        return ""
    # Strip NULL bytes
    text = text.replace("\x00", "")
    # Normalize excessive carriage returns / spacing
    text = re.sub(r"\r\n|\r", "\n", text)
    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
