import os
import math
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.schema import DocumentChunk
from src.embedder import BaseEmbedder


class VectorStore:
    """
    Local Vector Database wrapper powered by ChromaDB (with pure-Python fallback).
    Indexes DocumentChunks, manages embeddings, and provides similarity search.
    """

    def __init__(
        self,
        collection_name: str = "career_chunks",
        persist_dir: Optional[str] = "./chroma_db",
        embedder: Optional[BaseEmbedder] = None
    ):
        self.collection_name = collection_name
        self.embedder = embedder
        self.use_fallback = False
        self.fallback_chunks: List[DocumentChunk] = []

        try:
            import chromadb
            if persist_dir:
                Path(persist_dir).mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(path=persist_dir)
            else:
                self.client = chromadb.EphemeralClient()

            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            print("⚠️ ChromaDB package not detected. Using lightweight pure-Python vector store fallback.")
            self.use_fallback = True

    def add_chunks(self, chunks: List[DocumentChunk]):
        """
        Indexes a list of DocumentChunks into the vector database.
        """
        if not chunks:
            return

        if self.use_fallback:
            self.fallback_chunks.extend(chunks)
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.content for c in chunks]

        metadatas = []
        for c in chunks:
            meta = {
                "source_type": c.source_type,
                "title": c.title,
                "tech_stack": ", ".join(c.tech_stack),
                "domain_tags": ", ".join(c.domain_tags),
            }
            for k, v in c.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
            metadatas.append(meta)

        if self.embedder:
            embeddings = self.embedder.embed_documents(documents)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        return dot / (norm1 * norm2) if (norm1 > 0 and norm2 > 0) else 0.0

    def search(
        self,
        query: str,
        top_k: int = 5,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic cosine similarity search against indexed career chunks.
        """
        if self.use_fallback:
            query_vec = self.embedder.embed_query(query) if self.embedder else None
            scored_results = []

            for chunk in self.fallback_chunks:
                if source_type and chunk.source_type != source_type:
                    continue

                if query_vec and self.embedder:
                    chunk_vec = self.embedder.embed_query(chunk.content)
                    score = round(self._cosine_similarity(query_vec, chunk_vec), 4)
                else:
                    # Keyword overlap fallback score
                    words_q = set(query.lower().split())
                    words_c = set(chunk.content.lower().split())
                    overlap = len(words_q.intersection(words_c))
                    score = round(overlap / max(1, len(words_q)), 4)

                meta = {
                    "source_type": chunk.source_type,
                    "title": chunk.title,
                    "tech_stack": ", ".join(chunk.tech_stack),
                    "domain_tags": ", ".join(chunk.domain_tags),
                    **chunk.metadata
                }

                scored_results.append({
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "metadata": meta,
                    "similarity_score": score
                })

            scored_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return scored_results[:top_k]

        where_filter = {"source_type": source_type} if source_type else None

        if self.embedder:
            query_vector = self.embedder.embed_query(query)
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_filter
            )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )

        formatted_results = []
        if results and "ids" in results and results["ids"]:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                doc_text = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if "distances" in results and results["distances"] else 0.0
                similarity_score = round(1.0 - distance, 4)

                formatted_results.append({
                    "chunk_id": doc_id,
                    "content": doc_text,
                    "metadata": metadata,
                    "similarity_score": similarity_score
                })

        return formatted_results
