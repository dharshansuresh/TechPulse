# Automotive Engineering AI Assistant: Comprehensive Project Documentation

## 1. Executive Summary
The **Automotive Engineering AI Assistant** is an intelligent, domain-specific retrieval-augmented generation (RAG) platform tailored for automotive embedded software engineers and system architects. The system enables automated analysis, grounded question-answering with exact page citations, software component (SWC) extraction, ISO 26262 functional safety auditing, and revision comparison across 100+ page AUTOSAR High-Level Design (HLD) specifications.

## 2. Architectural Design
The architecture is structured in four decoupled tiers:
1. **Presentation Tier:** Streamlit Web Dashboard with 8 specialized navigation modules.
2. **Application Tier:** FastAPI REST backend providing asynchronous endpoints with Swagger/OpenAPI documentation.
3. **Intelligence & RAG Tier:** 
   - PyMuPDF text & table extractor with physical page tracking.
   - Recursive character chunker (500 tokens, 50-token overlap).
   - ChromaDB local embedded vector database.
   - Grounded LLM provider with citation grounding guardrails.
4. **Domain Analysis Tier:**
   - SWC & Port Taxonomy parser.
   - ISO 26262 Safety & Timing inconsistency auditor.
   - Architectural revision diffing engine.

## 3. Technology Stack & Rationale
- **Python 3.11+:** Industry standard for AI, NLP, and automotive data tooling.
- **FastAPI:** High-throughput asynchronous REST server with automatic schema validation (Pydantic v2).
- **Streamlit:** Interactive, responsive engineering UI.
- **PyMuPDF (fitz):** Sub-second PDF text and layout extraction with exact page coordinates.
- **ChromaDB:** Local, embedded, serverless vector store ensuring 100% offline data privacy for proprietary vehicle designs.
- **SQLite + SQLAlchemy:** Lightweight ACID-compliant relational metadata storage.
- **Pytest:** Automated testing framework.

## 4. User Manual & Step-by-Step Instructions
1. Run application: `python app.py --mode ui`
2. Open browser: `http://localhost:8501`
3. Load benchmark document: Click `Load AUTOSAR_Powertrain_Master_HLD_110Pages.pdf`
4. Ask question: Select suggested question and click `Ask Engineering Assistant`
5. Inspect results: View grounded answer, page citation badge, and retrieved evidence snippets.
