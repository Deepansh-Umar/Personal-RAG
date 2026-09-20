import json
import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.jd_parser import ParsedJobDescription
from src.recruiter_market_matrix import RECRUITER_DOMAINS


class FullContextSelectionEngine:
    """
    Autonomous Full-Context Selection Engine.
    Evaluates candidate's complete evidence store (scraped GitHub repos + YAML evidence)
    against target Job Descriptions and all recruiter market domains automatically.
    Filters out web utilities & empty repositories for AI/DL research roles.
    Strictly deduplicates projects by repository name and token similarity.
    """

    def __init__(self, data_dir: Optional[Path] = None, api_key: Optional[str] = None):
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data")
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                pass

    def _is_duplicate_project(self, new_proj: Any, existing_projects: List[Any]) -> bool:
        """
        Strict deduplication comparing GitHub URLs, repo names, and core topic signatures.
        """
        if isinstance(new_proj, dict):
            new_title = new_proj.get("title", "")
            new_url = (new_proj.get("github_url", "") or "").lower().rstrip('/')
        else:
            new_title = str(new_proj)
            new_url = ""

        new_lower = new_title.lower()
        topic_keywords = ["sentiment", "rag", "parkease", "shortener", "mlp", "housing", "diabetes", "hospital", "tesseract", "autohmpi", "leetcode"]

        new_tokens = set(re.findall(r'[a-zA-Z0-9]+', new_lower)) - {
            "project", "repo", "system", "assistant", "pipeline", "service", "app", "v2", "classification", "analysis", "framework", "tool"
        }

        for ex in existing_projects:
            if isinstance(ex, dict):
                ex_title = ex.get("title", "")
                ex_url = (ex.get("github_url", "") or "").lower().rstrip('/')
            else:
                ex_title = str(ex)
                ex_url = ""

            # 1. Direct GitHub URL match
            if new_url and ex_url and new_url == ex_url:
                return True

            ex_lower = ex_title.lower()

            # 2. Topic signature overlap (e.g. both refer to sentiment analysis or RAG)
            for kw in topic_keywords:
                if kw in new_lower and kw in ex_lower:
                    return True

            # 3. Token similarity check
            ex_tokens = set(re.findall(r'[a-zA-Z0-9]+', ex_lower)) - {
                "project", "repo", "system", "assistant", "pipeline", "service", "app", "v2", "classification", "analysis", "framework", "tool"
            }
            if not ex_tokens or not new_tokens:
                continue

            overlap = new_tokens.intersection(ex_tokens)
            if overlap and (len(overlap) / min(len(new_tokens), len(ex_tokens)) >= 0.5):
                return True

        return False

    def _load_all_candidate_projects(self) -> List[Dict[str, Any]]:
        all_projects = []

        # 1. Load from Master Project Knowledge Store if available
        master_store_path = self.data_dir / "master_project_store.yaml"
        if master_store_path.exists():
            with open(master_store_path, "r", encoding="utf-8") as f:
                raw_master = yaml.safe_load(f) or []
                for p in raw_master:
                    bullets = []
                    for b in p.get("resume_bullets", []):
                        bullets.append({"text": b} if isinstance(b, str) else b)

                    proj_obj = {
                        "id": p.get("id"),
                        "title": p.get("title"),
                        "github_url": p.get("github_url"),
                        "live_url": p.get("live_url", ""),
                        "tech_stack": p.get("tech_stack", []),
                        "bullets": bullets,
                        "domain_category": p.get("domain_category", ""),
                        "complexity_rating": p.get("complexity_rating", "")
                    }

                    if not self._is_duplicate_project(proj_obj, all_projects):
                        all_projects.append(proj_obj)

        # 2. Fallback to hand-curated career evidence if master store not loaded
        if not all_projects:
            yaml_path = self.data_dir / "career_evidence.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    for p in data.get("projects", []):
                        if not self._is_duplicate_project(p, all_projects):
                            all_projects.append(p)

        return all_projects

    def select_best_context_autonomously(self, parsed_jd: ParsedJobDescription) -> Dict[str, Any]:
        candidate_projects = self._load_all_candidate_projects()

        yaml_path = self.data_dir / "career_evidence.yaml"
        profile, education, experiences = {}, [], []
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                d = yaml.safe_load(f) or {}
                profile = d.get("profile", {})
                education = d.get("education", [])
                experiences = d.get("experiences", [])

        # Detect AI/DL/Research role
        title_lower = parsed_jd.title.lower()
        skills_lower = [s.lower() for s in parsed_jd.required_skills]
        is_dl_research_role = any(kw in title_lower or any(kw in s for s in skills_lower) for kw in ["deep learning", "research", "perception", "computer vision", "nlp", "machine learning", "ai"])

        # Filter out web utilities & empty repos for DL research roles
        if is_dl_research_role:
            filtered_projects = [
                p for p in candidate_projects
                if not any(web_kw in p.get("title", "").lower() or web_kw in p.get("id", "").lower()
                           for web_kw in ["url_shortener", "url shortener", "gcc_bose", "file_organizer", "tds", "resources"])
            ]
            if len(filtered_projects) >= 3:
                candidate_projects = filtered_projects

        if not self.client or not candidate_projects:
            jd_skills_lower = set(s.lower() for s in parsed_jd.required_skills)
            scored = []
            for p in candidate_projects:
                tech_set = set(t.lower() for t in p.get("tech_stack", []))
                p_title_lower = p.get("title", "").lower()
                overlap = len(jd_skills_lower.intersection(tech_set))

                if is_dl_research_role and any(ml_kw in p_title_lower or any(ml_kw in t for t in tech_set) for ml_kw in ["sentiment", "ml", "learning", "rag", "perception", "housing", "etl"]):
                    overlap += 5

                scored.append((overlap, p))

            scored.sort(key=lambda x: x[0], reverse=True)
            top_selected = [item[1] for item in scored[:4]]

            return {
                "profile": profile,
                "education": education,
                "experiences": experiences,
                "projects": top_selected,
                "matched_recruiter_domains": ["AI/ML", "Computer Vision", "Data Science"]
            }

        prompt = f"""
You are an Autonomous Executive Recruiter & AI Resume Architect.
Target Role: {parsed_jd.title} ({'DEEP LEARNING / AI RESEARCH ROLE' if is_dl_research_role else 'ENGINEERING ROLE'})
Company: {parsed_jd.company}

CRITICAL MANDATE FOR DL / AI RESEARCH ROLE:
DO NOT SELECT DUPLICATE PROJECTS OR BASIC WEB UTILITIES.
SELECT ONLY UNIQUE HIGH-IMPACT AI/ML, NLP, DATA PIPELINE, OR COMPLEX SYSTEM PROJECTS FROM THE LIST BELOW.

================ TARGET JOB DESCRIPTION ================
Role Title: {parsed_jd.title}
Required Skills: {', '.join(parsed_jd.required_skills)}
Core Responsibilities: {', '.join(parsed_jd.core_responsibilities[:4])}

================ CANDIDATE REPOSITORY INVENTORY ================
{yaml.dump(candidate_projects, default_flow_style=False)}

================ AUTONOMOUS INSTRUCTION ================
1. Select 3-4 UNIQUE candidate projects matching the role requirements.
2. Ensure ZERO duplicated project titles or duplicate repositories.

Return JSON formatted as:
{{
  "selected_project_ids": ["proj_phrase_sentiment_ml", "proj_personal_rag", "proj_parkease"],
  "matched_domains": ["AI, Machine Learning & LLMs", "Data Engineering & Big Data"],
  "selection_reasoning": "Detailed explanation of autonomous selection"
}}

Return ONLY valid JSON inside ```json ... ```.
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

            selected_ids = data.get("selected_project_ids", [])
            matched_projects = [p for p in candidate_projects if p.get("id") in selected_ids]

            if not matched_projects:
                matched_projects = candidate_projects[:4]

            return {
                "profile": profile,
                "education": education,
                "experiences": experiences,
                "projects": matched_projects,
                "matched_recruiter_domains": data.get("matched_domains", []),
                "selection_reasoning": data.get("selection_reasoning", "")
            }

        except Exception as e:
            print(f"⚠️ Autonomous selection error: {e}. Using score-based fallback.")
            return {
                "profile": profile,
                "education": education,
                "experiences": experiences,
                "projects": candidate_projects[:4],
                "matched_recruiter_domains": []
            }
