"""
Tests for DocumentService: upload, validation, duplicate detection,
path traversal defense, and deletion.
"""
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from database.repository import DocumentRepository
from backend.services.document_service import DocumentService
from core.security import sanitize_filename, validate_file_path


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()
    yield db
    db.close()


def test_path_traversal_prevention():
    base_dir = Path("C:/Tech Pulse/storage/uploads").resolve()
    dangerous_path = Path("C:/Tech Pulse/storage/uploads/../../windows/system32/cmd.exe")
    safe_path = Path("C:/Tech Pulse/storage/uploads/doc123_safe.pdf")

    assert validate_file_path(dangerous_path, base_dir) is False
    assert validate_file_path(safe_path, base_dir) is True


def test_filename_sanitization():
    clean1 = sanitize_filename("../../../etc/passwd.pdf")
    assert clean1 == "passwd.pdf"

    clean2 = sanitize_filename("my file <with> *special* ?chars?.pdf")
    assert " " not in clean2
    assert "<" not in clean2
    assert clean2.endswith(".pdf")


def test_duplicate_upload_detection(test_db):
    service = DocumentService()
    # Create valid minimal PDF bytes
    import pymupdf as fitz
    doc = fitz.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Test duplicate content")
    pdf_bytes = doc.tobytes()
    doc.close()

    # First upload
    rec1, is_dup1 = service.process_upload(pdf_bytes, "first.pdf", test_db)
    assert is_dup1 is False
    assert rec1.filename == "first.pdf"

    # Second upload with same bytes
    rec2, is_dup2 = service.process_upload(pdf_bytes, "second.pdf", test_db)
    assert is_dup2 is True
    assert rec2.id == rec1.id
