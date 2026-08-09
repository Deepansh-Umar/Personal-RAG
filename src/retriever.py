from typing import List, Dict, Any
from src.store import VectorStore
from src.jd_parser import ParsedJobDescription


class HybridRetriever:
    """
    Retrieves and ranks relevant career chunks for a parsed Job Description.
    Combines multi-angle vector queries with metadata skill boosting.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve_context(self, parsed_jd: ParsedJobDescription, top_k: int = 6) -> List[Dict[str, Any]]:
        retrieved_map: Dict[str, Dict[str, Any]] = {}

        # 1. Broad query using JD title and skills
        broad_query = f"{parsed_jd.title} requiring {', '.join(parsed_jd.required_skills)}"
        broad_results = self.vector_store.search(broad_query, top_k=top_k)
        for res in broad_results:
            retrieved_map[res["chunk_id"]] = res

        # 2. Granular queries per responsibility
        for resp in parsed_jd.key_responsibilities[:4]:
            results = self.vector_store.search(resp, top_k=2)
            for res in results:
                chunk_id = res["chunk_id"]
                if chunk_id not in retrieved_map:
                    retrieved_map[chunk_id] = res
                else:
                    # Boost score if retrieved in multiple queries
                    retrieved_map[chunk_id]["similarity_score"] = min(
                        1.0, retrieved_map[chunk_id]["similarity_score"] + 0.05
                    )

        # 3. Apply Metadata Skill Overlap Boost
        jd_skills_lower = set(s.lower() for s in parsed_jd.required_skills)
        for chunk_id, res in retrieved_map.items():
            chunk_tech = res["metadata"].get("tech_stack", "")
            if chunk_tech:
                chunk_skills = set(s.strip().lower() for s in chunk_tech.split(","))
                overlap = len(jd_skills_lower.intersection(chunk_skills))
                if overlap > 0:
                    # Grant 0.04 score boost per matching skill tag
                    res["similarity_score"] = min(1.0, res["similarity_score"] + (overlap * 0.04))

        # Sort by final boosted similarity score descending
        sorted_chunks = sorted(
            retrieved_map.values(),
            key=lambda x: x["similarity_score"],
            reverse=True
        )

        return sorted_chunks[:top_k]
