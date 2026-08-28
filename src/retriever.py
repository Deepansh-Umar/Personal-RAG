from typing import List, Dict, Any
from src.store import VectorStore
from src.jd_parser import ParsedJobDescription


class HybridRetriever:
    """
    Retrieves and ranks relevant career chunks for a parsed Job Description.
    Combines multi-angle vector queries with metadata skill boosting & keyword matching.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve_context(self, parsed_jd: ParsedJobDescription, top_k: int = 6) -> List[Dict[str, Any]]:
        retrieved_map: Dict[str, Dict[str, Any]] = {}

        skill_str = ", ".join(parsed_jd.required_skills) if parsed_jd.required_skills else "Software Engineering"
        broad_query = f"{parsed_jd.title} requiring {skill_str}"
        broad_results = self.vector_store.search(broad_query, top_k=top_k * 2)
        for res in broad_results:
            retrieved_map[res["chunk_id"]] = res

        for skill in parsed_jd.required_skills[:5]:
            results = self.vector_store.search(skill, top_k=2)
            for res in results:
                chunk_id = res["chunk_id"]
                if chunk_id not in retrieved_map:
                    retrieved_map[chunk_id] = res
                else:
                    retrieved_map[chunk_id]["similarity_score"] = min(
                        1.0, retrieved_map[chunk_id]["similarity_score"] + 0.08
                    )

        jd_skills_lower = set(s.lower() for s in parsed_jd.required_skills)
        for chunk_id, res in retrieved_map.items():
            content_lower = res["content"].lower()
            chunk_tech = res["metadata"].get("tech_stack", "").lower()

            overlap = sum(1 for skill in jd_skills_lower if skill in chunk_tech or skill in content_lower)
            if overlap > 0:
                res["similarity_score"] = min(1.0, round(res["similarity_score"] + (overlap * 0.12), 4))

        sorted_chunks = sorted(
            retrieved_map.values(),
            key=lambda x: x["similarity_score"],
            reverse=True
        )

        return sorted_chunks[:top_k]


class HierarchicalRetriever:
    """
    Hierarchical RAG Retriever for Resumes.
    1. Discovers and scores top matching PROJECTS dynamically from Vector DB.
    2. Gathers top matching EXPERIENCES and SKILLS.
    3. Guarantees complete project context without hardcoded fact sheets.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve_resume_context(self, parsed_jd: ParsedJobDescription, top_project_count: int = 4) -> Dict[str, Any]:
        jd_skills_str = ", ".join(parsed_jd.required_skills) if parsed_jd.required_skills else "Software Engineering"
        search_query = f"{parsed_jd.title} requiring {jd_skills_str}"

        # 1. Retrieve Candidate Projects
        project_results = self.vector_store.search(search_query, top_k=15, source_type="project")
        if not project_results:
            project_results = self.vector_store.search(search_query, top_k=15)

        # Group project chunks by title/name
        projects_map: Dict[str, List[Dict[str, Any]]] = {}
        for res in project_results:
            title = res["metadata"].get("title") or res["chunk_id"]
            if title not in projects_map:
                projects_map[title] = []
            projects_map[title].append(res)

        # 2. Retrieve Candidate Experiences
        experience_results = self.vector_store.search(search_query, top_k=6, source_type="experience")

        # 3. Retrieve Skills Categories
        skill_results = self.vector_store.search(search_query, top_k=5, source_type="skill")

        # Boost scores if required JD skills are present in content
        jd_skills_lower = set(s.lower() for s in parsed_jd.required_skills)
        for proj_title, chunks in projects_map.items():
            for c in chunks:
                content_lower = c["content"].lower()
                tech_lower = c["metadata"].get("tech_stack", "").lower()
                overlap = sum(1 for s in jd_skills_lower if s in content_lower or s in tech_lower)
                c["similarity_score"] = min(1.0, round(c["similarity_score"] + (overlap * 0.10), 4))

        # Select top project groups by max similarity score
        sorted_projects = sorted(
            projects_map.items(),
            key=lambda item: max(c["similarity_score"] for c in item[1]),
            reverse=True
        )[:top_project_count]

        selected_project_chunks = []
        for title, chunks in sorted_projects:
            selected_project_chunks.extend(chunks)

        return {
            "selected_projects": sorted_projects,
            "project_chunks": selected_project_chunks,
            "experience_chunks": experience_results,
            "skill_chunks": skill_results
        }
