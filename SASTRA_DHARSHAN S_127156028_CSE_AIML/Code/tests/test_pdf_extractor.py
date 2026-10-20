"""
Tests for PDF text extraction, page numbering preservation, and scanned PDF detection.
"""
import pytest
from pathlib import Path
import pymupdf as fitz
from document_processing.pdf_extractor import PDFExtractor, PDFExtractorError


def test_pdf_extraction_page_numbering():
    # Create synthetic 2-page PDF
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 50), "Page 1 Content: TorqueArbitrationSWC specification.", fontsize=12)
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 50), "Page 2 Content: ThrottleActuatorSWC specification.", fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()

    result = PDFExtractor.extract_from_bytes(pdf_bytes, filename="test_hld.pdf")

    assert result["page_count"] == 2
    assert len(result["pages"]) == 2
    assert result["pages"][0]["page_number"] == 1
    assert "TorqueArbitrationSWC" in result["pages"][0]["text"]
    assert result["pages"][1]["page_number"] == 2
    assert "ThrottleActuatorSWC" in result["pages"][1]["text"]
    assert result["ocr_warning"] is False


def test_empty_pdf_error():
    with pytest.raises(PDFExtractorError):
        PDFExtractor.extract_from_bytes(b"", filename="empty.pdf")


def test_malformed_pdf_error():
    with pytest.raises(PDFExtractorError):
        PDFExtractor.extract_from_bytes(b"%PDF-1.4 corrupt garbage data", filename="corrupt.pdf")


def test_file_hash_calculation():
    data1 = b"%PDF-1.4 test 1"
    data2 = b"%PDF-1.4 test 2"
    h1 = PDFExtractor.calculate_file_hash(data1)
    h2 = PDFExtractor.calculate_file_hash(data2)
    assert len(h1) == 64
    assert h1 != h2
    assert h1 == PDFExtractor.calculate_file_hash(data1)
