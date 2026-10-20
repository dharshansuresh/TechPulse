"""
Document Summarizer for AUTOSAR HLD documents.
Produces overall architectural summary, section breakdown, and topic extraction.
"""
import re
from typing import Dict, Any, List
from rag.retriever import retriever
from rag.llm_provider import llm_provider, LLMResult
from rag.prompt_templates import SUMMARY_PROMPT_TEMPLATE
from core.logging_config import logger


class DocumentSummarizer:
    def summarize_document(
        self,
        document_id: str,
        filename: str,
        total_pages: int,
    ) -> Dict[str, Any]:
        """
        Generate architectural summary for a document.
        Uses LLM if available, otherwise generates a comprehensive deterministic summary.
        """
        # Retrieve key chunks across the document
        chunks = retriever.retrieve(
            query="AUTOSAR architecture overview software components interfaces RTE BSW diagnostics safety",
            top_k=8,
            document_id=document_id,
        )

        if not chunks:
            # Try retrieving any chunks for this document
            chunks = retriever.retrieve(
                query="system overview scope introduction",
                top_k=6,
                document_id=document_id,
            )

        context_parts = [f"[Page {c['page_number']}]: {c['text']}" for c in chunks]
        context_str = "\n\n".join(context_parts)

        # Architectural topics detection
        detected_topics = self._detect_topics(context_str)

        info = llm_provider.get_active_provider_info()
        if info["provider"] != "retrieval_only":
            try:
                prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context_str)
                llm_res = llm_provider.generate(
                    prompt=prompt,
                    system_prompt="You are an expert Automotive Systems Architect. Provide structured, cited summaries.",
                    context_chunks=chunks,
                )
                if not llm_res.is_retrieval_only:
                    return {
                        "document_id": document_id,
                        "filename": filename,
                        "total_pages": total_pages,
                        "summary_markdown": llm_res.text,
                        "major_topics": detected_topics,
                        "provider": llm_res.provider,
                        "is_retrieval_only": False,
                    }
            except Exception as e:
                logger.warning(f"LLM summarization failed: {e}. Using deterministic summary.")

        # Deterministic summary fallback
        summary_md = self._build_deterministic_summary(filename, total_pages, chunks, detected_topics)
        return {
            "document_id": document_id,
            "filename": filename,
            "total_pages": total_pages,
            "summary_markdown": summary_md,
            "major_topics": detected_topics,
            "provider": "Deterministic Architectural Analyzer",
            "is_retrieval_only": True,
        }

    def _detect_topics(self, text: str) -> List[Dict[str, Any]]:
        topics = []
        catalog = [
            ("Application Software Components (SWC)", r"SWC|Software Component|Application Component", "High"),
            ("Runtime Environment (RTE)", r"RTE|Rte_Write|Rte_Read|Rte_Call", "High"),
            ("Basic Software (BSW)", r"BSW|Basic Software|OS|ComM|PduR|CanIf", "Medium"),
            ("Controller Area Network (CAN) / Ethernet", r"CAN|CAN FD|Ethernet|SOME/IP|FlexRay", "High"),
            ("Functional Safety (ISO 26262)", r"ASIL|ISO 26262|E2E|Safety Goal|FSR|TSR", "High"),
            ("Diagnostics & Fault Memory (UDS / DEM)", r"UDS|ISO 14229|DEM|DTC|DID|0x22|Diagnostic", "Medium"),
            ("Memory Management (NVRAM / NvM)", r"NvM|NVRAM|EEPROM|Flash", "Low"),
            ("Cybersecurity (ISO 21434)", r"ISO 21434|TARA|Crypto|SecOC|MAC|Security", "Medium"),
        ]
        for name, pattern, relevance in catalog:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                topics.append({
                    "topic": name,
                    "occurrences": matches,
                    "relevance": relevance,
                })
        return topics

    def _build_deterministic_summary(
        self,
        filename: str,
        total_pages: int,
        chunks: List[Dict[str, Any]],
        topics: List[Dict[str, Any]],
    ) -> str:
        lines = [
            f"## Architectural Design Document Summary: `{filename}`",
            "",
            f"- **Document Name:** {filename}",
            f"- **Total Pages:** {total_pages}",
            f"- **Analysis Engine:** Grounded Semantic Extraction (Deterministic)",
            "",
            "### 1. Major Architectural Domains Identified",
        ]
        if topics:
            for t in topics:
                lines.append(f"- **{t['topic']}** (Mention frequency: {t['occurrences']}, Priority: {t['relevance']})")
        else:
            lines.append("- General Automotive Software Design")

        lines.extend([
            "",
            "### 2. Key Architecture Excerpts & Citations",
        ])

        for i, ch in enumerate(chunks[:4], 1):
            lines.append(f"#### Excerpt {i} [Doc: {filename}, Page: {ch['page_number']}]:")
            # First 3 lines
            sample = "\n".join(ch["text"].split("\n")[:4])
            lines.append(f"> {sample}")
            lines.append("")

        lines.extend([
            "### 3. Reviewer Verification Notice",
            "> **Engineering Notice:** The extracted summaries and identified topics are candidate extractions. "
            "System architects must confirm exact interface definitions and safety goals prior to release."
        ])

        return "\n".join(lines)


summarizer = DocumentSummarizer()
