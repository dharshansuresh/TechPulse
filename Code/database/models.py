"""
SQLAlchemy ORM models for document management, chunk metadata, audit logs, and analysis runs.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="uploaded")  # uploaded, indexing, indexed, error
    ocr_warning = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    version_tag = Column(String(64), nullable=True, default="v1.0")
    domain = Column(String(128), nullable=True, default="Automotive Architecture")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    chunks = relationship("ChunkRecord", back_populates="document", cascade="all, delete-orphan")


class ChunkRecord(Base):
    __tablename__ = "chunks"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)
    content_snippet = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now)

    document = relationship("DocumentRecord", back_populates="chunks")


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    action = Column(String(64), nullable=False)  # UPLOAD, INDEX, DELETE, SEARCH, CHAT, ANALYSIS
    document_id = Column(String(36), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="SUCCESS")
    details = Column(Text, nullable=True)


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), nullable=True, index=True)
    second_document_id = Column(String(36), nullable=True)
    analysis_type = Column(String(64), nullable=False)  # summary, components, inconsistencies, compare
    created_at = Column(DateTime, default=utc_now)
    result_json = Column(Text, nullable=False)
