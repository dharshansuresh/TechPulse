"""
Document management REST API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import DocumentRepository
from backend.services.document_service import document_service
from backend.schemas.document_schema import (
    DocumentResponse,
    DocumentListResponse,
    UploadResponse,
    IndexResponse,
)
from core.logging_config import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    domain: str = Form("Powertrain"),
    version_tag: str = Form("v1.0"),
    db: Session = Depends(get_db),
):
    """Upload and process a PDF document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files (.pdf) are permitted.",
        )

    content = await file.read()
    try:
        record, is_duplicate = document_service.process_upload(
            file_bytes=content,
            original_filename=file.filename,
            db=db,
            domain=domain,
            version_tag=version_tag,
        )
        msg = "Document uploaded and indexed successfully." if not is_duplicate else "Duplicate document identified. Returning existing record."
        return UploadResponse(
            message=msg,
            document=DocumentResponse.model_validate(record),
            is_duplicate=is_duplicate,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during upload.")


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """Retrieve all uploaded documents and their indexing statuses."""
    docs = DocumentRepository.list_documents(db)
    return DocumentListResponse(
        count=len(docs),
        documents=[DocumentResponse.model_validate(d) for d in docs],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve metadata for a specific document."""
    doc = DocumentRepository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return DocumentResponse.model_validate(doc)


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document, its disk file, and associated vector records."""
    success = document_service.delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return {"message": f"Document {document_id} and its vector indices were deleted successfully."}


@router.post("/{document_id}/index", response_model=IndexResponse)
def index_document(document_id: str, db: Session = Depends(get_db)):
    """Re-index a document into the ChromaDB vector database."""
    doc = DocumentRepository.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        count = document_service.index_document(document_id, db)
        return IndexResponse(
            document_id=document_id,
            filename=doc.filename,
            status="indexed",
            chunks_indexed=count,
            message=f"Indexed {count} chunks successfully.",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
