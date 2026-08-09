import re
from typing import List
from pydantic import BaseModel, Field


class ParsedJobDescription(BaseModel):
    title: str
    company: str = "Target Company"
    required_skills: List[str] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    domain_keywords: List[str] = Field(default_factory=list)
    full_text: str


class HeuristicJDParser:
    """
    Parses a raw Job Description using regex heuristics & keyword extraction.
    (Can also be backed by LLM parsing in generator.py).
    """

    KNOWN_TECH_KEYWORDS = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "qdrant", "chromadb", "pgvector", "postgresql", "redis", "celery",
        "aws", "docker", "kubernetes", "microservices", "rag", "llm",
        "vector search", "crdt", "websockets", "ci/cd", "unit testing"
    ]

    def parse(self, jd_text: str, title: str = "Target Role", company: str = "Company") -> ParsedJobDescription:
        lowered = jd_text.lower()
        
        # 1. Extract matched technology keywords
        found_skills = []
        for tech in self.KNOWN_TECH_KEYWORDS:
            if re.search(r'\b' + re.escape(tech) + r'\b', lowered):
                # Capitalize nicely
                found_skills.append(tech.title() if len(tech) > 3 else tech.upper())

        # 2. Extract key sentences containing action words
        lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
        responsibilities = []
        for line in lines:
            if re.match(r'^[-•*]\s*', line) or any(verb in line.lower() for verb in ["build", "design", "lead", "develop", "optimize", "architect"]):
                cleaned = re.sub(r'^[-•*]\s*', '', line)
                if len(cleaned) > 20:
                    responsibilities.append(cleaned)

        return ParsedJobDescription(
            title=title,
            company=company,
            required_skills=list(set(found_skills)),
            key_responsibilities=responsibilities[:8],
            domain_keywords=list(set(found_skills)),
            full_text=jd_text
        )
