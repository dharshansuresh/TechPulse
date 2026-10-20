"""
PDF text extraction and validation service using PyMuPDF (fitz).
Preserves 1-indexed original page numbers and detects scanned/image-only PDFs.
"""
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
import fitz  # PyMuPDF
from core.logging_config import logger
from core.security import sanitize_document_text


class PDFExtractorError(Exception):
    """Raised when PDF extraction fails or file is invalid."""
    pass


class PDFExtractor:
    @staticmethod
    def calculate_file_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 checksum for deduplication."""
        hasher = hashlib.sha256()
        hasher.update(file_bytes)
        return hasher.hexdigest()

    @staticmethod
    def extract_from_bytes(
        file_bytes: bytes,
        filename: str = "document.pdf",
    ) -> Dict[str, Any]:
        """
        Extract text page by page from raw bytes.
        Returns dictionary containing:
          - page_count: int
          - pages: List[Dict[str, Any]] (page_number, text, char_count, image_count)
          - is_scanned: bool
          - total_char_count: int
          - ocr_warning: bool
          - file_hash: str
          - metadata: Dict[str, Any]
        """
        if not file_bytes:
            raise PDFExtractorError("PDF file is empty (0 bytes).")

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF stream for {filename}: {e}")
            raise PDFExtractorError(f"Malformed or corrupt PDF file: {str(e)}")

        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise PDFExtractorError("PDF file contains 0 pages.")

        extracted_pages: List[Dict[str, Any]] = []
        total_chars = 0
        total_images = 0

        for page_idx in range(page_count):
            page_num = page_idx + 1  # 1-indexed for citations
            try:
                page = doc.load_page(page_idx)
                raw_text = page.get_text("text") or ""
                cleaned_text = sanitize_document_text(raw_text)
                image_list = page.get_images(full=True)
                img_count = len(image_list)

                char_count = len(cleaned_text)
                total_chars += char_count
                total_images += img_count

                extracted_pages.append({
                    "page_number": page_num,
                    "text": cleaned_text,
                    "char_count": char_count,
                    "image_count": img_count,
                })
            except Exception as e:
                logger.warning(f"Error reading page {page_num} of {filename}: {e}")
                extracted_pages.append({
                    "page_number": page_num,
                    "text": "",
                    "char_count": 0,
                    "image_count": 0,
                    "error": str(e),
                })

        pdf_meta = doc.metadata or {}
        doc.close()

        # Check for scanned or image-only PDF
        # If there are images and avg characters per page < 40, or total chars < 60 across multiple pages
        avg_chars_per_page = total_chars / max(page_count, 1)
        is_scanned = (avg_chars_per_page < 40 and total_images > 0) or (total_chars == 0 and total_images > 0)
        ocr_warning = is_scanned or (total_chars < 50)

        file_hash = PDFExtractor.calculate_file_hash(file_bytes)

        return {
            "filename": filename,
            "page_count": page_count,
            "total_char_count": total_chars,
            "total_images": total_images,
            "is_scanned": is_scanned,
            "ocr_warning": ocr_warning,
            "file_hash": file_hash,
            "pages": extracted_pages,
            "metadata": {
                "title": pdf_meta.get("title", ""),
                "author": pdf_meta.get("author", ""),
                "subject": pdf_meta.get("subject", ""),
            },
        }

    @classmethod
    def extract_from_file(cls, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF file on disk."""
        if not file_path.exists():
            raise PDFExtractorError(f"File not found: {file_path}")
        with open(file_path, "rb") as f:
            content = f.read()
        return cls.extract_from_bytes(content, filename=file_path.name)
