import json
import os
import re
from typing import List, Optional
from pydantic import BaseModel


class ParsedJobDescription(BaseModel):
    title: str = "Software Engineer"
    company: str = "Target Company"
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    core_responsibilities: List[str] = []
    seniority_level: str = "Mid-Level"


class LLMJobDescriptionParser:
    """
    Structured LLM Parser for Job Descriptions.
    Replaces brittle heuristic keyword matching with full semantic understanding.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                pass

    def parse(self, raw_jd_text: str, default_title: str = "Software Engineer", default_company: str = "Target Company") -> ParsedJobDescription:
        if not raw_jd_text or len(raw_jd_text.strip()) < 20:
            return ParsedJobDescription(title=default_title, company=default_company)

        # Basic fallback parser if no LLM key
        if not self.client:
            skills = []
            known_tech = [
                "Python", "PyTorch", "TensorFlow", "Scikit-learn", "FastAPI", "Flask",
                "React", "TypeScript", "PostgreSQL", "Redis", "Celery", "Docker",
                "Kubernetes", "AWS", "LLM", "NLP", "RAG", "SQL", "Git", "Pandas", "NumPy"
            ]
            for tech in known_tech:
                if re.search(r'\b' + re.escape(tech) + r'\b', raw_jd_text, re.IGNORECASE):
                    skills.append(tech)

            return ParsedJobDescription(
                title=default_title,
                company=default_company,
                required_skills=skills if skills else ["Python", "Software Engineering"],
                core_responsibilities=[line.strip() for line in raw_jd_text.split("\n") if len(line.strip()) > 30][:5]
            )

        prompt = f"""
Parse the following Job Description into a clean JSON object with these keys:
- "title": (string) exact role title
- "company": (string) company name if mentioned, else "Target Company"
- "required_skills": (list of strings) mandatory tech stack and skills
- "preferred_skills": (list of strings) nice-to-have skills
- "core_responsibilities": (list of strings) top 5 responsibilities
- "seniority_level": (string) e.g. Intern, Junior, Mid, Senior

JOB DESCRIPTION:
{raw_jd_text}

Return ONLY valid JSON wrapped in ```json ... ```.
"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            json_str = match.group(1) if match else text
            data = json.loads(json_str)

            return ParsedJobDescription(
                title=data.get("title", default_title),
                company=data.get("company", default_company),
                required_skills=data.get("required_skills", []),
                preferred_skills=data.get("preferred_skills", []),
                core_responsibilities=data.get("core_responsibilities", []),
                seniority_level=data.get("seniority_level", "Mid-Level")
            )
        except Exception as e:
            print(f"⚠️ LLM JD Parser error: {e}. Falling back to basic parser.")
            return ParsedJobDescription(title=default_title, company=default_company)
