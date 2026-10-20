"""
ChromaDB vector store manager.
Handles persistent collection storage, metadata indexing, document-filtered queries,
and clean deletion of vectors.
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings
from core.logging_config import logger
from document_processing.embeddings import embedding_service


class ChromaVectorStore:
    def __init__(
        self,
        persist_dir: str = str(settings.CHROMA_PERSIST_DIR),
        collection_name: str = settings.CHROMA_COLLECTION_NAME,
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_collection(self):
        if self._collection is None:
            logger.info(f"Connecting to ChromaDB at: {self.persist_dir}")
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Index or re-index a list of text chunks.
        Automatically generates embeddings if not already attached.
        """
        if not chunks:
            return 0

        collection = self._get_collection()

        doc_ids_to_clean = list({c["document_id"] for c in chunks})
        for d_id in doc_ids_to_clean:
            self.delete_by_document_id(d_id)

        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]
        metadatas = [
            {
                "document_id": str(c["document_id"]),
                "filename": str(c["filename"]),
                "page_number": int(c["page_number"]),
                "chunk_index": int(c["chunk_index"]),
                "char_count": int(c.get("char_count", len(c["text"]))),
            }
            for c in chunks
        ]

        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = embedding_service.embed_texts(texts)

        # Batch insert into ChromaDB
        batch_size = 200
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_texts = texts[i : i + batch_size]
            batch_metadatas = metadatas[i : i + batch_size]
            batch_embeddings = embeddings[i : i + batch_size]

            collection.add(
                ids=batch_ids,
                documents=batch_texts,
                metadatas=batch_metadatas,
                embeddings=batch_embeddings,
            )

        logger.info(f"Successfully indexed {len(ids)} chunks into ChromaDB.")
        return len(ids)

    def query(
        self,
        query_text: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for the most semantically relevant chunks.
        Returns list of dicts with: chunk_id, text, metadata, distance, score.
        """
        collection = self._get_collection()
        if collection.count() == 0:
            return []

        query_vector = embedding_service.embed_query(query_text)

        where_filter = None
        if document_id:
            where_filter = {"document_id": document_id}
        elif document_ids and len(document_ids) == 1:
            where_filter = {"document_id": document_ids[0]}
        elif document_ids and len(document_ids) > 1:
            where_filter = {"document_id": {"$in": document_ids}}

        try:
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=min(top_k, max(1, collection.count())),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

        retrieved: List[Dict[str, Any]] = []
        if results and "ids" in results and results["ids"]:
            ids_list = results["ids"][0]
            docs_list = results["documents"][0]
            meta_list = results["metadatas"][0]
            dist_list = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids_list)

            for cid, doc_text, meta, dist in zip(ids_list, docs_list, meta_list, dist_list):
                # Cosine distance: 0 = exact match, 2 = opposite. Similarity = 1 - (dist / 2) or 1 - dist
                similarity_score = max(0.0, 1.0 - float(dist))
                retrieved.append({
                    "chunk_id": cid,
                    "text": doc_text,
                    "filename": meta.get("filename", "Unknown"),
                    "page_number": int(meta.get("page_number", 1)),
                    "document_id": meta.get("document_id", ""),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                    "distance": float(dist),
                    "score": round(similarity_score, 4),
                })

        return retrieved

    def delete_by_document_id(self, document_id: str) -> bool:
        """Remove all chunks associated with a document_id."""
        collection = self._get_collection()
        try:
            collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document_id: {document_id}")
            return True
        except Exception as e:
            logger.warning(f"Note deleting vectors for {document_id}: {e}")
            return False

    def count(self) -> int:
        return self._get_collection().count()


vector_store = ChromaVectorStore()
