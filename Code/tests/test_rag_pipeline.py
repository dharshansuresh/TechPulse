"""
Tests for RAG QA Pipeline, citation formatting, insufficient evidence handling, and LLM fallback.
"""
from rag.qa_pipeline import rag_pipeline
from rag.llm_provider import llm_provider, LLMResult


def test_rag_pipeline_empty_query():
    res = rag_pipeline.ask("")
    assert "cannot be empty" in res["answer"].lower()
    assert res["evidence_sufficient"] is False


def test_rag_retrieval_only_synthesis():
    chunks = [
        {
            "chunk_id": "test_c1",
            "filename": "powertrain_v1.pdf",
            "page_number": 2,
            "text": "TorqueArbitrationSWC provides Pp_TorqueCommand with If_TorqueCommand interface.",
            "score": 0.88,
        }
    ]

    res = llm_provider._synthesize_retrieval_only("What is the provided port?", chunks)
    assert res.is_retrieval_only is True
    assert "[Doc: powertrain_v1.pdf, Page: 2]" in res.text
    assert "TorqueArbitrationSWC" in res.text


def test_insufficient_evidence_detection():
    # If a query has zero matching chunks
    res = rag_pipeline.ask("What is the quantum computing algorithm used in the ECU?", top_k=1)
    # Either answer indicates insufficient or no relevant evidence
    assert res["evidence_sufficient"] is False or "insufficient" in res["answer"].lower() or "no relevant" in res["answer"].lower()
