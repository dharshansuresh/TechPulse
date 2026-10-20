"""
Tests for text chunking and metadata preservation.
"""
from document_processing.chunker import DocumentChunker


def test_chunker_metadata_preservation():
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
    pages = [
        {"page_number": 1, "text": "Short page 1 text describing SWC."},
        {"page_number": 2, "text": "Page 2 text with Rte_Write_Pp_TorqueCommand and CAN 0x1A4."},
    ]

    chunks = chunker.chunk_extracted_pages("doc_123", "powertrain.pdf", pages)

    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["document_id"] == "doc_123"
    assert chunks[0]["filename"] == "powertrain.pdf"
    assert chunks[1]["page_number"] == 2
    assert "Rte_Write_Pp_TorqueCommand" in chunks[1]["text"]


def test_chunker_handles_empty_pages():
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=30)
    pages = [
        {"page_number": 1, "text": ""},
        {"page_number": 2, "text": "   "},
        {"page_number": 3, "text": "Valid content on page 3"},
    ]
    chunks = chunker.chunk_extracted_pages("doc_empty", "empty.pdf", pages)
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 3
