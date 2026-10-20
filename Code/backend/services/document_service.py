"""
Document Service coordinating PDF upload, validation, extraction,
chunking, persistent vector indexing, and deletion lifecycle.
"""
import uuid
from pathlib import Path
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from core.config import settings
from core.logging_config import logger
from core.security import sanitize_filename, validate_file_path, validate_pdf_content
from database.repository import DocumentRepository
from document_processing.pdf_extractor import PDFExtractor, PDFExtractorError
from document_processing.chunker import DocumentChunker
from rag.vector_store import vector_store


class DocumentService:
    def __init__(self):
        self.chunker = DocumentChunker()
        self.vector_store = vector_store

    def process_upload(
        self,
        file_bytes: bytes,
        original_filename: str,
        db: Session,
        domain: str = "Powertrain",
        version_tag: str = "v1.0",
    ) -> Tuple[Dict[str, Any], bool]:
        """
        Validates, deduplicates, saves, and indexes a PDF document.
        Returns (document_record_dict, is_duplicate).
        """
        # 1. Security & content validation
        valid, msg = validate_pdf_content(file_bytes)
        if not valid:
            DocumentRepository.log_audit(
                db, action="UPLOAD", status="FAILURE", details=f"Validation failed: {msg}"
            )
            raise ValueError(msg)

        # 2. Check for duplicate via SHA256 hash
        file_hash = PDFExtractor.calculate_file_hash(file_bytes)
        existing = DocumentRepository.get_document_by_hash(db, file_hash)
        if existing:
            DocumentRepository.log_audit(
                db,
                action="UPLOAD",
                status="DUPLICATE",
                document_id=existing.id,
                details=f"Duplicate file uploaded: {original_filename} matches existing {existing.filename}",
            )
            return existing, True

        # 3. Safe filename and path handling
        clean_name = sanitize_filename(original_filename)
        doc_id = str(uuid.uuid4())
        safe_disk_filename = f"{doc_id}_{clean_name}"
        target_path = settings.UPLOAD_DIR / safe_disk_filename

        if not validate_file_path(target_path, settings.UPLOAD_DIR):
            raise ValueError("Path traversal attempt detected.")

        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # 4. Extract pages and inspect for scanned/image-only
        try:
            extraction = PDFExtractor.extract_from_bytes(file_bytes, filename=clean_name)
        except PDFExtractorError as e:
            target_path.unlink(missing_ok=True)
            raise ValueError(f"PDF extraction error: {e}")

        # 5. Persist document metadata in SQLite
        doc_record = DocumentRepository.create_document(
            db=db,
            doc_id=doc_id,
            filename=clean_name,
            stored_path=str(target_path),
            file_hash=file_hash,
            file_size_bytes=len(file_bytes),
            page_count=extraction["page_count"],
            ocr_warning=extraction["ocr_warning"],
            version_tag=version_tag,
            domain=domain,
        )

        DocumentRepository.log_audit(
            db,
            action="UPLOAD",
            status="SUCCESS",
            document_id=doc_id,
            details=f"Uploaded '{clean_name}' ({extraction['page_count']} pages, OCR Warning: {extraction['ocr_warning']})",
        )

        # 6. Index document chunks
        self.index_document(doc_id=doc_id, db=db, extraction_data=extraction)

        return doc_record, False

    def index_document(
        self,
        doc_id: str,
        db: Session,
        extraction_data: Dict[str, Any] = None,
    ) -> int:
        """
        Chunks and creates embeddings for persistent storage in ChromaDB and SQLite.
        """
        record = DocumentRepository.get_document_by_id(db, doc_id)
        if not record:
            raise ValueError(f"Document {doc_id} not found.")

        DocumentRepository.update_document_status(db, doc_id, status="indexing")

        try:
            if extraction_data is None:
                file_path = Path(record.stored_path)
                extraction_data = PDFExtractor.extract_from_file(file_path)

            pages = extraction_data.get("pages", [])
            chunks = self.chunker.chunk_extracted_pages(
                document_id=doc_id,
                filename=record.filename,
                pages=pages,
            )

            if not chunks:
                DocumentRepository.update_document_status(
                    db,
                    doc_id,
                    status="indexed_empty",
                    error_message="Document contained no extractable textual content.",
                )
                return 0

            # 1. Index in ChromaDB
            count_indexed = self.vector_store.index_chunks(chunks)

            # 2. Save metadata in SQLite
            DocumentRepository.save_chunk_records(db, doc_id=doc_id, chunks=chunks)

            # 3. Update status
            DocumentRepository.update_document_status(
                db,
                doc_id=doc_id,
                status="indexed",
                page_count=extraction_data["page_count"],
                ocr_warning=extraction_data["ocr_warning"],
            )

            DocumentRepository.log_audit(
                db,
                action="INDEX",
                status="SUCCESS",
                document_id=doc_id,
                details=f"Indexed {count_indexed} chunks for {record.filename}",
            )
            return count_indexed

        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            DocumentRepository.update_document_status(
                db, doc_id, status="failed", error_message=str(e)
            )
            DocumentRepository.log_audit(
                db, action="INDEX", status="FAILURE", document_id=doc_id, details=str(e)
            )
            raise

    def delete_document(self, doc_id: str, db: Session) -> bool:
        """
        Deletes vector records, physical disk file, and database records.
        """
        record = DocumentRepository.get_document_by_id(db, doc_id)
        if not record:
            return False

        # 1. Delete vectors from ChromaDB
        self.vector_store.delete_by_document_id(doc_id)

        # 2. Delete file on disk
        try:
            file_path = Path(record.stored_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not remove file on disk {record.stored_path}: {e}")

        # 3. Delete from SQLite (cascades to chunks)
        DocumentRepository.delete_document(db, doc_id)

        DocumentRepository.log_audit(
            db,
            action="DELETE",
            status="SUCCESS",
            document_id=doc_id,
            details=f"Deleted document {record.filename} and associated vectors.",
        )
        return True


document_service = DocumentService()
