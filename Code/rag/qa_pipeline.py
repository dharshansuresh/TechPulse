"""
End-to-End RAG Question-Answering Pipeline.
Grounded in uploaded AUTOSAR HLD documents with exact page citations.
"""
import re
from typing import Dict, Any, List, Optional
from core.config import settings
from core.logging_config import logger
from rag.retriever import retriever
from rag.prompt_templates import AUTOSAR_RAG_SYSTEM_PROMPT, RAG_USER_PROMPT_TEMPLATE
from rag.llm_provider import llm_provider, LLMResult


class RAGQAPipeline:
    def __init__(self):
        self.retriever = retriever
        self.llm = llm_provider

    def ask(
        self,
        question: str,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: int = settings.RETRIEVAL_TOP_K,
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline:
        1. Retrieve context chunks from vector DB
        2. Format context with document and page markers
        3. Dispatch to configured LLM (or offline synthesis)
        4. Assemble citations and evidence inspection objects
        """
        if not question or not question.strip():
            return {
                "question": question or "",
                "answer": "Question cannot be empty.",
                "citations": [],
                "evidence_chunks": [],
                "evidence_sufficient": False,
                "is_retrieval_only": True,
                "provider": "None",
            }

        # 1. Retrieve evidence
        chunks = self.retriever.retrieve(
            query=question.strip(),
            top_k=top_k,
            document_id=document_id,
            document_ids=document_ids,
        )

        # Check if chunks are empty, below minimum relevance threshold, or have zero lexical overlap
        max_score = max([c.get("score", 0.0) for c in chunks]) if chunks else 0.0
        query_terms = [
            w.lower()
            for w in re.findall(r"[a-zA-Z]{4,}", question)
            if w.lower() not in {"what", "which", "where", "when", "does", "used", "that", "this", "with", "from", "have", "been"}
        ]
        combined_text = " ".join([c.get("text", "") for c in chunks]).lower()
        has_overlap = any(t in combined_text for t in query_terms) if query_terms else True

        if not chunks or max_score < 0.25 or not has_overlap:
            return {
                "question": question,
                "answer": (
                    "The uploaded document evidence is insufficient to answer this question. "
                    "The retrieved passages do not specify information related to your query."
                ),
                "citations": [],
                "evidence_chunks": chunks if chunks else [],
                "evidence_sufficient": False,
                "is_retrieval_only": True,
                "provider": "Semantic Retriever",
                "model": "None",
            }

        # 2. Format context with document and page numbers
        formatted_context_parts = []
        citations_set = set()
        citations_list = []

        for ch in chunks:
            doc_name = ch["filename"]
            page_no = ch["page_number"]
            formatted_context_parts.append(
                f"[Source Document: {doc_name} | Page: {page_no}]\n{ch['text']}\n"
            )
            citation_tuple = (doc_name, page_no)
            if citation_tuple not in citations_set:
                citations_set.add(citation_tuple)
                citations_list.append({
                    "filename": doc_name,
                    "page_number": page_no,
                    "citation_str": f"[Doc: {doc_name}, Page: {page_no}]",
                })

        context_str = "\n---\n".join(formatted_context_parts)
        user_prompt = RAG_USER_PROMPT_TEMPLATE.format(context=context_str, question=question.strip())

        # 3. Generate answer via LLM Provider (or offline synthesis)
        llm_result: LLMResult = self.llm.generate(
            prompt=user_prompt,
            system_prompt=AUTOSAR_RAG_SYSTEM_PROMPT,
            context_chunks=chunks,
        )

        # 4. Check if answer indicates insufficient evidence
        ans_lower = llm_result.text.lower()
        insufficient_markers = [
            "evidence is insufficient",
            "insufficient evidence",
            "not mentioned in the context",
            "not specified in the context",
            "retrieved passages do not specify",
            "no relevant document evidence",
        ]
        evidence_sufficient = not any(m in ans_lower for m in insufficient_markers)

        return {
            "question": question,
            "answer": llm_result.text,
            "citations": citations_list,
            "evidence_chunks": chunks,
            "evidence_sufficient": evidence_sufficient,
            "is_retrieval_only": llm_result.is_retrieval_only,
            "provider": llm_result.provider,
            "model": llm_result.model,
            "privacy_notice": llm_result.privacy_notice,
        }


rag_pipeline = RAGQAPipeline()
