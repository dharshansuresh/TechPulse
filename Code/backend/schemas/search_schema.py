"""
Pydantic schemas for technical search and retrieval endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Keyword or technical search term")
    document_id: Optional[str] = Field(None, description="Optional document ID filter")
    top_k: Optional[int] = Field(6, ge=1, le=50, description="Max results")


class SearchResultItem(BaseModel):
    chunk_id: str
    filename: str
    page_number: int
    score: float
    text: str
    document_id: str


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResultItem]
