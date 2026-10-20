"""
Semantic and hybrid document retriever.
Retrieves relevant text passages with citations and confidence metrics.
"""
from typing import List, Dict, Any, Optional
from core.config import settings
from core.logging_config import logger
from rag.vector_store import vector_store


class AutomotiveRetriever:
    def __init__(self, top_k: int = settings.RETRIEVAL_TOP_K):
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Query the persistent vector store and return ranked evidence passages.
        """
        k = top_k or self.top_k
        logger.info(f"Retrieving top {k} chunks for query: '{query[:80]}'")

        chunks = vector_store.query(
            query_text=query,
            top_k=k,
            document_id=document_id,
            document_ids=document_ids,
        )

        filtered = [ch for ch in chunks if ch.get("score", 0.0) >= min_score]
        return filtered

    def search_keywords(
        self,
        keyword: str,
        document_id: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Perform targeted technical keyword search with citation preservation.
        """
        results = self.retrieve(query=keyword, top_k=top_k, document_id=document_id)
        # Highlight keyword in snippets
        for r in results:
            text = r["text"]
            r["keyword_matches"] = text.lower().count(keyword.lower())
        return results


retriever = AutomotiveRetriever()
