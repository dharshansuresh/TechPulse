"""
Repository for database CRUD operations and audit logging.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database.models import (
    DocumentRecord,
    ChunkRecord,
    AuditLogRecord,
    AnalysisRecord,
    utc_now,
)
from core.logging_config import logger


class DocumentRepository:
    @staticmethod
    def create_document(
        db: Session,
        doc_id: str,
        filename: str,
        stored_path: str,
        file_hash: str,
        file_size_bytes: int,
        page_count: int,
        ocr_warning: bool = False,
        version_tag: str = "v1.0",
        domain: str = "Powertrain",
    ) -> DocumentRecord:
        record = DocumentRecord(
            id=doc_id,
            filename=filename,
            stored_path=stored_path,
            file_hash=file_hash,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            status="uploaded",
            ocr_warning=ocr_warning,
            version_tag=version_tag,
            domain=domain,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_document_by_id(db: Session, doc_id: str) -> Optional[DocumentRecord]:
        return db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()

    @staticmethod
    def get_document_by_hash(db: Session, file_hash: str) -> Optional[DocumentRecord]:
        return db.query(DocumentRecord).filter(DocumentRecord.file_hash == file_hash).first()

    @staticmethod
    def list_documents(db: Session) -> List[DocumentRecord]:
        return db.query(DocumentRecord).order_by(DocumentRecord.created_at.desc()).all()

    @staticmethod
    def update_document_status(
        db: Session,
        doc_id: str,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
        ocr_warning: Optional[bool] = None,
    ) -> Optional[DocumentRecord]:
        record = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
        if not record:
            return None
        record.status = status
        record.updated_at = utc_now()
        if error_message is not None:
            record.error_message = error_message
        if page_count is not None:
            record.page_count = page_count
        if ocr_warning is not None:
            record.ocr_warning = ocr_warning
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def delete_document(db: Session, doc_id: str) -> bool:
        record = db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True

    @staticmethod
    def save_chunk_records(
        db: Session,
        doc_id: str,
        chunks: List[Dict[str, Any]],
    ) -> int:
        # First remove any prior chunks for this doc (for re-indexing)
        db.query(ChunkRecord).filter(ChunkRecord.document_id == doc_id).delete()
        
        chunk_objs = []
        for ch in chunks:
            chunk_objs.append(
                ChunkRecord(
                    id=ch["chunk_id"],
                    document_id=doc_id,
                    page_number=ch["page_number"],
                    chunk_index=ch["chunk_index"],
                    char_count=len(ch["text"]),
                    content_snippet=ch["text"][:200],
                )
            )
        db.bulk_save_objects(chunk_objs)
        db.commit()
        return len(chunk_objs)

    @staticmethod
    def log_audit(
        db: Session,
        action: str,
        status: str = "SUCCESS",
        document_id: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLogRecord:
        try:
            entry = AuditLogRecord(
                action=action,
                status=status,
                document_id=document_id,
                details=details,
            )
            db.add(entry)
            db.commit()
            return entry
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            db.rollback()
            return None

    @staticmethod
    def save_analysis(
        db: Session,
        analysis_id: str,
        analysis_type: str,
        result_json: str,
        document_id: Optional[str] = None,
        second_document_id: Optional[str] = None,
    ) -> AnalysisRecord:
        rec = AnalysisRecord(
            id=analysis_id,
            analysis_type=analysis_type,
            result_json=result_json,
            document_id=document_id,
            second_document_id=second_document_id,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_latest_analysis(
        db: Session,
        document_id: str,
        analysis_type: str,
    ) -> Optional[AnalysisRecord]:
        return (
            db.query(AnalysisRecord)
            .filter(
                AnalysisRecord.document_id == document_id,
                AnalysisRecord.analysis_type == analysis_type,
            )
            .order_by(AnalysisRecord.created_at.desc())
            .first()
        )
