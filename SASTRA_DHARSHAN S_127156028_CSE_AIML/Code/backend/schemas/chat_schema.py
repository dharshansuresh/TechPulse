"""
Pydantic schemas for Chat and RAG QA endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CitationItem(BaseModel):
    filename: str
    page_number: int
    citation_str: str


class EvidenceChunkItem(BaseModel):
    chunk_id: str
    filename: str
    page_number: int
    score: float
    text: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Natural language question about AUTOSAR HLD")
    document_id: Optional[str] = Field(None, description="Optional target document ID to filter query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of target document IDs")
    top_k: Optional[int] = Field(4, ge=1, le=20, description="Number of evidence chunks to retrieve")


class ChatResponse(BaseModel):
    question: str
    answer: str
    citations: List[CitationItem]
    evidence_chunks: List[EvidenceChunkItem]
    evidence_sufficient: bool
    is_retrieval_only: bool
    provider: str
    model: Optional[str] = None
    privacy_notice: Optional[str] = None
