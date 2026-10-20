"""
Architectural analysis, summarization, component extraction,
inconsistency detection, and document comparison endpoints.
"""
import uuid
import json
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import DocumentRepository
from backend.schemas.analysis_schema import (
    SummaryRequest,
    SummaryResponse,
    ComponentsRequest,
    ComponentsResponse,
    InconsistenciesRequest,
    InconsistenciesResponse,
    CompareRequest,
    CompareResponse,
)
from analysis.summarizer import summarizer
from analysis.component_extractor import component_extractor
from analysis.inconsistency_detector import inconsistency_detector
from analysis.document_comparator import document_comparator
from core.logging_config import logger

router = APIRouter(prefix="/analysis", tags=["Architectural Analysis"])


@router.post("/summary", response_model=SummaryResponse)
def generate_summary(req: SummaryRequest, db: Session = Depends(get_db)):
    """Generate high-level architectural summary of an AUTOSAR document."""
    doc = DocumentRepository.get_document_by_id(db, req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    res = summarizer.summarize_document(
        document_id=doc.id,
        filename=doc.filename,
        total_pages=doc.page_count,
    )

    # Save to analysis table
    DocumentRepository.save_analysis(
        db=db,
        analysis_id=str(uuid.uuid4()),
        analysis_type="summary",
        result_json=json.dumps(res),
        document_id=doc.id,
    )

    return SummaryResponse(**res)


@router.post("/components", response_model=ComponentsResponse)
def extract_components(req: ComponentsRequest, db: Session = Depends(get_db)):
    """Extract candidate software components, ports, and interfaces."""
    doc = DocumentRepository.get_document_by_id(db, req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    res = component_extractor.extract_components(
        document_id=doc.id,
        filename=doc.filename,
    )

    DocumentRepository.save_analysis(
        db=db,
        analysis_id=str(uuid.uuid4()),
        analysis_type="components",
        result_json=json.dumps(res),
        document_id=doc.id,
    )

    return ComponentsResponse(**res)


@router.post("/inconsistencies", response_model=InconsistenciesResponse)
def detect_inconsistencies(req: InconsistenciesRequest, db: Session = Depends(get_db)):
    """Detect potential architectural mismatches and unmapped ports."""
    doc = DocumentRepository.get_document_by_id(db, req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Primary document not found.")

    sec_name = None
    if req.secondary_document_id:
        sec_doc = DocumentRepository.get_document_by_id(db, req.secondary_document_id)
        if sec_doc:
            sec_name = sec_doc.filename

    res = inconsistency_detector.detect_inconsistencies(
        document_id=doc.id,
        filename=doc.filename,
        secondary_document_id=req.secondary_document_id,
        secondary_filename=sec_name,
    )

    DocumentRepository.save_analysis(
        db=db,
        analysis_id=str(uuid.uuid4()),
        analysis_type="inconsistencies",
        result_json=json.dumps(res),
        document_id=doc.id,
        second_document_id=req.secondary_document_id,
    )

    return InconsistenciesResponse(**res)


@router.post("/compare", response_model=CompareResponse)
def compare_documents(req: CompareRequest, db: Session = Depends(get_db)):
    """Compare two documents or versions and highlight additions, removals, and changes."""
    doc_a = DocumentRepository.get_document_by_id(db, req.doc_a_id)
    doc_b = DocumentRepository.get_document_by_id(db, req.doc_b_id)

    if not doc_a or not doc_b:
        raise HTTPException(status_code=404, detail="One or both documents not found.")

    res = document_comparator.compare_documents(
        doc_a_id=doc_a.id,
        doc_a_name=doc_a.filename,
        doc_b_id=doc_b.id,
        doc_b_name=doc_b.filename,
    )

    DocumentRepository.save_analysis(
        db=db,
        analysis_id=str(uuid.uuid4()),
        analysis_type="compare",
        result_json=json.dumps(res),
        document_id=doc_a.id,
        second_document_id=doc_b.id,
    )

    return CompareResponse(**res)
