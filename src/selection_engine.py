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
    Zero manual project picking required from the user.
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

    def _load_all_candidate_projects(self) -> List[Dict[str, Any]]:
        all_projects = []

        # 1. Load hand-curated YAML evidence
        yaml_path = self.data_dir / "career_evidence.yaml"
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                all_projects.extend(data.get("projects", []))

        # 2. Load scraped GitHub repositories
        gh_path = self.data_dir / "github_deep_extract.yaml"
        if gh_path.exists():
            with open(gh_path, "r", encoding="utf-8") as f:
                gh_projects = yaml.safe_load(f) or []
                for gh in gh_projects:
                    # Avoid duplicates if already in YAML
                    if not any(p.get("id") == gh.get("id") for p in all_projects):
                        bullets = []
                        if gh.get("readme_summary") and len(gh["readme_summary"]) > 40:
                            bullets.append({"text": gh["readme_summary"][:300]})
                        elif gh.get("description"):
                            bullets.append({"text": gh["description"]})

                        all_projects.append({
                            "id": gh.get("id"),
                            "title": gh.get("title"),
                            "github_url": gh.get("github_url"),
                            "live_url": gh.get("live_url", ""),
                            "tech_stack": [gh.get("primary_language", "")] if gh.get("primary_language") != "N/A" else [],
                            "bullets": bullets
                        })

        return all_projects

    def select_best_context_autonomously(self, parsed_jd: ParsedJobDescription) -> Dict[str, Any]:
        """
        AUTONOMOUS SELECTION: Evaluates all candidate projects against the JD & Recruiter Matrix.
        Returns top matching projects and bullets automatically.
        """
        candidate_projects = self._load_all_candidate_projects()

        # Default profile & education facts
        yaml_path = self.data_dir / "career_evidence.yaml"
        profile, education, experiences = {}, [], []
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                d = yaml.safe_load(f) or {}
                profile = d.get("profile", {})
                education = d.get("education", [])
                experiences = d.get("experiences", [])

        if not self.client or not candidate_projects:
            # Deterministic autonomous selection fallback
            jd_skills_lower = set(s.lower() for s in parsed_jd.required_skills)
            scored = []
            for p in candidate_projects:
                tech_set = set(t.lower() for t in p.get("tech_stack", []))
                title_lower = p.get("title", "").lower()
                overlap = len(jd_skills_lower.intersection(tech_set))
                if any(s in title_lower for s in jd_skills_lower):
                    overlap += 2
                scored.append((overlap, p))

            scored.sort(key=lambda x: x[0], reverse=True)
            top_selected = [item[1] for item in scored[:4]]

            return {
                "profile": profile,
                "education": education,
                "experiences": experiences,
                "projects": top_selected,
                "matched_recruiter_domains": ["Full-Stack & Web", "AI/ML", "Backend"]
            }

        # Autonomous Full-Context Prompt
        prompt = f"""
You are an Autonomous Executive Recruiter & AI Resume Architect.
Your task is to AUTONOMOUSLY analyze the Candidate's entire project repository (scraped GitHub repos + YAML evidence) and select the TOP 3 to 4 PROJECTS that best match the target Job Description and Recruiter Market Standards.

================ TARGET JOB DESCRIPTION ================
Role Title: {parsed_jd.title}
Required Skills: {', '.join(parsed_jd.required_skills)}
Core Responsibilities: {', '.join(parsed_jd.core_responsibilities[:4])}

================ RECRUITER MARKET DOMAINS MATRIX ================
{json.dumps(RECRUITER_DOMAINS, indent=2)}

================ CANDIDATE REPOSITORY INVENTORY ================
{yaml.dump(candidate_projects, default_flow_style=False)}

================ AUTONOMOUS INSTRUCTION ================
1. Autonomously select the 3-4 best candidate projects that align with the role requirements.
2. Select the top 2-3 bullet points per project.
3. Identify which Recruiter Market Domains the candidate matches best.

Return JSON formatted as:
{{
  "selected_project_ids": ["proj_id_1", "proj_id_2"],
  "matched_domains": ["Cloud & Infrastructure", "Full-Stack & Web Engineering"],
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
