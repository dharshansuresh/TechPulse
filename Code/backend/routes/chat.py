"""
Chat and RAG Question-Answering REST API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import DocumentRepository
from backend.schemas.chat_schema import ChatRequest, ChatResponse
from rag.qa_pipeline import rag_pipeline
from core.logging_config import logger

router = APIRouter(prefix="/chat", tags=["Chat & RAG"])


@router.post("/ask", response_model=ChatResponse)
def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask a question against indexed AUTOSAR HLD documents.
    Returns grounded answer with document and page citations.
    """
    try:
        # Log query to audit log
        DocumentRepository.log_audit(
            db,
            action="CHAT_QUERY",
            status="SUCCESS",
            document_id=request.document_id,
            details=f"Question: {request.question[:100]}",
        )

        res = rag_pipeline.ask(
            question=request.question,
            document_id=request.document_id,
            document_ids=request.document_ids,
            top_k=request.top_k,
        )

        return ChatResponse(
            question=res["question"],
            answer=res["answer"],
            citations=res["citations"],
            evidence_chunks=res["evidence_chunks"],
            evidence_sufficient=res["evidence_sufficient"],
            is_retrieval_only=res["is_retrieval_only"],
            provider=res["provider"],
            model=res.get("model"),
            privacy_notice=res.get("privacy_notice"),
        )
    except Exception as e:
        logger.error(f"Chat pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"QA pipeline error: {str(e)}")
