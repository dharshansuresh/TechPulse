"""
Tests for FastAPI endpoints: /health, /documents, /chat/ask, /search.
"""
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_list_documents_endpoint():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "documents" in data


def test_search_endpoint():
    response = client.post("/search", json={"query": "SWC", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "total_results" in data
    assert data["query"] == "SWC"


def test_chat_ask_endpoint():
    response = client.post("/chat/ask", json={"question": "What is TorqueArbitrationSWC?", "top_k": 2})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "evidence_chunks" in data
