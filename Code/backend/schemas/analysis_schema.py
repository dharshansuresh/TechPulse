"""
Pydantic schemas for architectural analysis endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    document_id: str


class SummaryResponse(BaseModel):
    document_id: str
    filename: str
    total_pages: int
    summary_markdown: str
    major_topics: List[Dict[str, Any]]
    provider: str
    is_retrieval_only: bool


class ComponentsRequest(BaseModel):
    document_id: str


class ComponentPort(BaseModel):
    name: str
    port_type: str
    interface: Optional[str] = None
    details: Optional[str] = None
    citation: Optional[str] = None


class SoftwareComponentItem(BaseModel):
    name: str
    component_type: str
    ports: List[ComponentPort] = []
    cycle_time_ms: Optional[str] = "Not Specified"
    asil_level: Optional[str] = "Unspecified"
    status: str = "Candidate - Requires Human Verification"
    citation: Optional[str] = None


class ComponentsResponse(BaseModel):
    document_id: str
    filename: str
    component_count: int
    components: List[SoftwareComponentItem]
    extraction_method: str
    status_notice: str


class InconsistenciesRequest(BaseModel):
    document_id: str
    secondary_document_id: Optional[str] = None


class InconsistencyFinding(BaseModel):
    category: str
    severity: str
    title: str
    affected_swc: str
    details: str
    evidence_citation: str
    verification_label: str


class InconsistenciesResponse(BaseModel):
    document_id: str
    filename: str
    findings_count: int
    findings: List[InconsistencyFinding]
    compliance_disclaimer: str


class CompareRequest(BaseModel):
    doc_a_id: str
    doc_b_id: str


class CompareResponse(BaseModel):
    doc_a: Dict[str, str]
    doc_b: Dict[str, str]
    summary: Dict[str, int]
    added_components: List[Dict[str, Any]]
    removed_components: List[Dict[str, Any]]
    modified_components: List[Dict[str, Any]]
    verification_note: str
