"""
Embedding generation service with Sentence Transformers and graceful offline fallback.
Produces normalized 384-dimensional dense vectors.
"""
import hashlib
import numpy as np
from typing import List
from core.config import settings
from core.logging_config import logger


class EmbeddingService:
    _instance = None
    _model = None
    _use_fallback = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self.vector_dim = 384

    def _load_model(self):
        if self._model is not None or self._use_fallback:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer embedding model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer '{self.model_name}' ({e}). "
                "Engaging deterministic local fallback embedding engine."
            )
            self._use_fallback = True

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a list of strings."""
        if not texts:
            return []

        self._load_model()

        if self._model is not None and not self._use_fallback:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error during SentenceTransformer inference: {e}. Falling back.")

        # Fallback deterministic bag-of-words hashing embedding
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding vector for a single query string."""
        vectors = self.embed_texts([query])
        return vectors[0] if vectors else [0.0] * self.vector_dim

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic lightweight 384-dimensional pseudo-semantic embedding.
        Uses character n-grams and token hashes normalized by L2 norm.
        Allows retrieval and tests to work completely offline without model downloads.
        """
        vec = np.zeros(self.vector_dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()

        for word in words:
            # Hash word into bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.vector_dim
            sign = 1.0 if (h // self.vector_dim) % 2 == 0 else -1.0
            vec[idx] += sign

        # N-grams for partial match
        for i in range(len(text) - 3):
            trigram = text[i : i + 3].lower()
            h = int(hashlib.sha1(trigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.vector_dim
            vec[idx] += 0.2

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# Singleton instance
embedding_service = EmbeddingService()
