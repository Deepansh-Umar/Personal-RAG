import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class LaTeXExporter:
    """
    Renders high-density, ATS-optimized LaTeX (.tex) resumes matching Jake's Resume standard template.
    Enforces single primary education and em-dash (---) contact separators.
    """

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path or (Path(__file__).parent.parent / "templates" / "resume_template.tex")

    def _escape_latex(self, text: str) -> str:
        if not text:
            return ""
        text = str(text)
        text = text.replace('\\', '\\textbackslash{}')
        text = text.replace('&', '\\&')
        text = text.replace('%', '\\%')
        text = text.replace('$', '\\$')
        text = text.replace('#', '\\#')
        text = text.replace('_', '\\_')
        text = text.replace('~', '\\textasciitilde{}')
        text = text.replace('^', '\\textasciicircum{}')
        return text

    def export_latex(self, candidate_data: Dict[str, Any], output_path: Path) -> str:
        if not self.template_path.exists():
            raise FileNotFoundError(f"LaTeX template not found at {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        profile = candidate_data.get("profile", {})
        education = candidate_data.get("education", [])
        experiences = candidate_data.get("experiences", [])
        projects = candidate_data.get("projects", [])

        # 1. Header Replacements
        template_str = template_str.replace("{{ NAME }}", self._escape_latex(profile.get("name", "Deepansh Umar")))
        template_str = template_str.replace("{{ PHONE }}", self._escape_latex(profile.get("phone", "(+91) 9581730273")))
        template_str = template_str.replace("{{ EMAIL }}", profile.get("email", "umardeepansh@gmail.com"))
        template_str = template_str.replace("{{ LINKEDIN }}", profile.get("linkedin", "https://linkedin.com/in/deepansh-umar"))
        template_str = template_str.replace("{{ GITHUB }}", profile.get("github", "https://github.com/Deepansh-Umar"))

        # 2. Education Block (STRICT SINGLE PRIMARY EDUCATION RULE)
        primary_edu = [e for e in education if e.get("is_primary")] or (education[:1] if education else [])
        edu_items = []
        for edu in primary_edu:
            inst = self._escape_latex(edu.get("institution", "Indian Institute of Technology Madras"))
            deg = self._escape_latex(edu.get("degree", "Bachelor of Science in Data Science and Applications"))
            dates = self._escape_latex(edu.get("dates", "2024 – Present"))
            cgpa = self._escape_latex(edu.get("cgpa", "9.23 / 10.0"))
            detail = f"CGPA: {cgpa}" if cgpa else ""

            edu_items.append(
                f"    \\resumeSubheading\n"
                f"      {{{inst}}}{{{dates}}}\n"
                f"      {{{deg}}}{{{detail}}}"
            )
        template_str = template_str.replace("{{ EDUCATION_BLOCK }}", "\n".join(edu_items))

        # 3. Experience Block (Including Conglomerate IT & e-DAM Mentor)
        exp_items = []
        for exp in experiences:
            role = self._escape_latex(exp.get("role", ""))
            org = self._escape_latex(exp.get("organization", ""))
            dates = self._escape_latex(exp.get("dates", ""))

            bullets = exp.get("bullets", [])
            bullet_tex = []
            for b in bullets:
                b_text = b.get("text", "") if isinstance(b, dict) else str(b)
                bullet_tex.append(f"        \\resumeBullet{{{self._escape_latex(b_text)}}}")

            bullets_str = "\n".join(bullet_tex)
            exp_items.append(
                f"    \\resumeSubheading\n"
                f"      {{{org}}}{{{dates}}}\n"
                f"      {{{role}}}{{}}\n"
                f"      \\resumeItemListStart\n"
                f"{bullets_str}\n"
                f"      \\resumeItemListEnd"
            )
        template_str = template_str.replace("{{ EXPERIENCES_BLOCK }}", "\n".join(exp_items))

        # 4. Projects Block
        proj_items = []
        for proj in projects:
            title = self._escape_latex(proj.get("title", ""))
            tech_list = proj.get("tech_stack", [])
            tech_str = self._escape_latex(", ".join(tech_list)) if isinstance(tech_list, list) else self._escape_latex(str(tech_list))
            repo_url = proj.get("github_url", "")
            live_url = proj.get("live_url", "")

            link_part = f"\\href{{{repo_url}}}{{\\underline{{GitHub}}}}"
            if live_url:
                link_part += f" $|$ \\href{{{live_url}}}{{\\underline{{Live Demo}}}}"

            bullets = proj.get("bullets", [])
            bullet_tex = []
            for b in bullets:
                b_text = b.get("text", "") if isinstance(b, dict) else str(b)
                bullet_tex.append(f"        \\resumeBullet{{{self._escape_latex(b_text)}}}")

            bullets_str = "\n".join(bullet_tex)
            proj_items.append(
                f"    \\resumeProjectHeading\n"
                f"      {{\\textbf{{{title}}} $|$ \\emph{{{tech_str}}}}}{{{link_part}}}\n"
                f"      \\resumeItemListStart\n"
                f"{bullets_str}\n"
                f"      \\resumeItemListEnd"
            )
        template_str = template_str.replace("{{ PROJECTS_BLOCK }}", "\n".join(proj_items))

        # 5. Skills Block
        template_str = template_str.replace("{{ LANGUAGES }}", "Python, Java, SQL, JavaScript, HTML/CSS, React, Bash, C/C++")
        template_str = template_str.replace("{{ AIML_SKILLS }}", "Claude API, Gemini API, PyTorch, Scikit-Learn, LightGBM, XGBoost, NLP, TF-IDF, RAG, ChromaDB")
        template_str = template_str.replace("{{ BACKEND_SKILLS }}", "Flask, REST APIs, FastAPI, PostgreSQL, Redis, Celery, Chrome Extensions")
        template_str = template_str.replace("{{ DATABASE_SKILLS }}", "PostgreSQL, MySQL, SQLite, Redis")
        template_str = template_str.replace("{{ TOOLS_SKILLS }}", "Git, GitHub, Docker, LinkedIn Recruiter, Ceipal, Postman, Render, Vercel")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template_str)

        return template_str
