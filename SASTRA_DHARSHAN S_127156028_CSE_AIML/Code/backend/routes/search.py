"""
Technical keyword and passage search REST API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.session import get_db
from database.repository import DocumentRepository
from backend.schemas.search_schema import SearchRequest, SearchResponse, SearchResultItem
from rag.retriever import retriever
from core.logging_config import logger

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
def search_documents(request: SearchRequest, db: Session = Depends(get_db)):
    """Search for technical terms and view relevant passages with citations."""
    try:
        DocumentRepository.log_audit(
            db,
            action="SEARCH",
            status="SUCCESS",
            document_id=request.document_id,
            details=f"Query: {request.query[:100]}",
        )

        results = retriever.retrieve(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )

        items = [
            SearchResultItem(
                chunk_id=r["chunk_id"],
                filename=r["filename"],
                page_number=r["page_number"],
                score=r["score"],
                text=r["text"],
                document_id=r.get("document_id", ""),
            )
            for r in results
        ]

        return SearchResponse(
            query=request.query,
            total_results=len(items),
            results=items,
        )
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
