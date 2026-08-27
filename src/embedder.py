import numpy as np
from abc import ABC, abstractmethod
from typing import List, Union


class BaseEmbedder(ABC):
    """
    Abstract interface for text embedding providers.
    """
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Local HuggingFace embedding model (all-MiniLM-L6-v2 by default).
    Includes a lightweight hash-vector fallback if sentence-transformers PyTorch packages are loading.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.use_fallback = False
        try:
            # pyrefly: ignore [missing-import] 
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except Exception:
            print("⚠️ sentence-transformers not detected. Using lightweight internal vectorizer fallback.")
            self.use_fallback = True

    def _hash_vector(self, text: str, dim: int = 384) -> List[float]:
        """Generates a deterministic 384-dimensional normalized word-count vector for fallback testing."""
        vec = np.zeros(dim)
        words = text.lower().split()
        for word in words:
            idx = abs(hash(word)) % dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.use_fallback:
            return [self._hash_vector(t) for t in texts]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        if self.use_fallback:
            return self._hash_vector(text)
        embedding = self.model.encode(text, show_progress_bar=False)
        return embedding.tolist()
