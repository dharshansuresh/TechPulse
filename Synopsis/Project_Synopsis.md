# SASTRA DEEMED TO BE UNIVERSITY
### School of Computing | Department of Computer Science & Engineering (AI & ML)
### PROJECT SYNOPSIS (ACADEMIC YEAR 2025–2026)

---

**Project Title:** Automotive Engineering AI Assistant: AUTOSAR HLD Intelligence Platform  
**Candidate Name:** DHARSHAN S  
**Register Number:** 127156028  
**Department:** Computer Science & Engineering (Artificial Intelligence & Machine Learning)  
**Institution:** SASTRA Deemed to be University, Thanjavur  
**Domain:** Applied Artificial Intelligence / Retrieval-Augmented Generation (RAG) / Automotive Systems  

---

### 1. ABSTRACT
Modern automotive systems require 100+ page AUTOSAR High-Level Design (HLD) specifications detailing Software Components (SWCs), execution timing, and ISO 26262 safety requirements. Manual review is tedious, and generic cloud AI models hallucinate and compromise data privacy. This project develops an offline, privacy-preserving AI assistant using PyMuPDF, ChromaDB, and Retrieval-Augmented Generation (RAG). The system provides grounded answers with exact page citations, reverse-engineers SWC taxonomies, audits safety boundaries, and compares revisions across 110-page enterprise HLD specifications.

---

### 2. PROBLEM STATEMENT
- **Information Overload:** Reviewing 100+ page HLD specifications manually consumes hours and leads to human error.
- **AI Hallucinations:** Generic cloud LLMs invent plausible but fictitious signal names, timing rates, and ASIL ratings.
- **Lack of Traceability:** Existing search tools lack physical page citations required for automotive compliance audits.
- **Data Privacy & IP Protection:** Proprietary vehicle designs cannot be uploaded to public third-party cloud servers.

---

### 3. OBJECTIVES
1. **Automated Document Ingestion:** Page-aware parsing and chunking of 100+ page automotive HLD PDFs.
2. **Grounded RAG Q&A Engine:** Sub-second technical answers with 100% citation precision (citing exact page numbers).
3. **Automated SWC & Port Extraction:** Reverse-engineering of AUTOSAR SWCs, cycle times (10ms), and P/R ports.
4. **Static Safety Auditing:** Automated detection of ISO 26262 ASIL boundary violations and timing sampling conflicts.
5. **Architectural Revision Diffing:** Semantic comparison between document versions (v1.0 vs. v2.0).

---

### 4. SYSTEM ARCHITECTURE & MODULES
- **Architecture:** 4-Tier pipeline consisting of a Streamlit UI, FastAPI REST backend, ChromaDB local vector database, and local RAG synthesis engine.
- **8 System Modules:** (1) Document Library & Ingestion, (2) Grounded Q&A Assistant, (3) Technical Search, (4) Architectural Summary, (5) SWC & Port Extraction, (6) Inconsistency & Safety Checks, (7) Revision Comparator, (8) Export Center (CSV/JSON).

---

### 5. TECHNICAL SPECIFICATIONS & VERIFIED RESULTS
- **Technologies:** Python 3.10+, FastAPI, Streamlit, PyMuPDF (`fitz`), ChromaDB, SQLite, Pytest.
- **Pytest Automated Tests:** **20 / 20 Test Cases Passed (100% Pass Rate)**.
- **Benchmark Evaluation:** Tested on an authentic **110-Page AUTOSAR HLD Document** (124 vector chunks).
  - **Retrieval Hit Rate:** **100.0%** (10/10 Queries)
  - **Citation Precision:** **100.0%**
  - **Hallucination Rate:** **0.0%**
  - **Average Response Latency:** **1.4 seconds**

---

```text
Student Signature: _______________________          Supervisor Signature: _______________________
DHARSHAN S (127156028)                             Project Guide / Faculty Advisor
```
