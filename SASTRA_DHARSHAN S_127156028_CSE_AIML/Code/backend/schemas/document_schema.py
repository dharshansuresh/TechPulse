"""
Pydantic schemas for Document Management endpoints.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_size_bytes: int
    page_count: int
    status: str
    ocr_warning: bool
    version_tag: Optional[str] = "v1.0"
    domain: Optional[str] = "Powertrain"
    created_at: datetime
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    count: int
    documents: List[DocumentResponse]


class UploadResponse(BaseModel):
    message: str
    document: DocumentResponse
    is_duplicate: bool = False


class IndexResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunks_indexed: int
    message: str
