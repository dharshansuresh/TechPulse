# Model Prompts, RAG Guardrails & Hyperparameters Configuration

## 1. RAG Grounded Q&A Prompt
```text
You are an expert automotive software systems engineer specializing in AUTOSAR Classic/Adaptive platforms and ISO 26262 functional safety. You answer technical questions strictly using retrieved HLD document evidence. You never hallucinate signal names, SWC interfaces, or ASIL ratings. Always provide page-grounded citations.
```

### Hyperparameters:
- **Temperature:** 0.1 (low temperature ensures deterministic, non-hallucinated responses)
- **Top-K Chunk Depth:** 4 chunks (default), adjustable up to 8
- **Chunk Size:** 500 tokens
- **Chunk Overlap:** 50 tokens (ensures sentence continuity across chunk boundaries)
- **Vector Metric:** Cosine Distance / Cosine Similarity

## 2. SWC & Port Extraction Prompt
```text
Extract structured candidate AUTOSAR Software Components (SWCs), execution periods, ASIL ratings, and Provided/Required ports from HLD tables and architectural diagrams.
```

## 3. ISO 26262 Safety & Timing Checker Prompt
```text
Audit SWC port connections for ASIL decomposition mismatches (ASIL-D to QM without safety wrapper) and timing sampling conflicts (e.g., 10ms periodic sender to 100ms periodic receiver).
```
