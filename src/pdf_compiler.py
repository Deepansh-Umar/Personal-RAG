import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


class PDFCompilerEngine:
    """
    Compiles resumes into high-density, ATS-friendly PDF files matching Jake's Resume LaTeX layout.
    Enforces single primary education and em-dash (&mdash;) contact separators.
    """

    def __init__(self, edge_path: Optional[str] = None):
        self.edge_path = edge_path or r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

    def _generate_print_html(self, candidate_data: Dict[str, Any]) -> str:
        profile = candidate_data.get("profile", {})
        education = candidate_data.get("education", [])
        experiences = candidate_data.get("experiences", [])
        projects = candidate_data.get("projects", [])

        name = profile.get("name", "Deepansh Umar")
        email = profile.get("email", "umardeepansh@gmail.com")
        phone = profile.get("phone", "(+91) 9581730273")
        linkedin = profile.get("linkedin", "https://linkedin.com/in/deepansh-umar")
        github = profile.get("github", "https://github.com/Deepansh-Umar")

        # Single primary education
        primary_edu = [e for e in education if e.get("is_primary")] or (education[:1] if education else [])
        edu_items = []
        for edu in primary_edu:
            inst = edu.get("institution", "Indian Institute of Technology Madras")
            deg = edu.get("degree", "Bachelor of Science in Data Science and Applications")
            dates = edu.get("dates", "2024 – Present")
            cgpa = edu.get("cgpa", "9.23 / 10.0")
            detail = f"CGPA: {cgpa}" if cgpa else ""

            edu_items.append(f"""
            <div class="row">
                <div><strong>{inst}</strong> &mdash; <em>{deg}</em></div>
                <div class="right-align">{dates} | {detail}</div>
            </div>
            """)
        edu_html = "\n".join(edu_items)

        exp_items = []
        for exp in experiences:
            org = exp.get("organization", "")
            role = exp.get("role", "")
            dates = exp.get("dates", "")
            bullets = exp.get("bullets", [])

            b_html = "\n".join(f"<li>{b.get('text', '') if isinstance(b, dict) else str(b)}</li>" for b in bullets)

            exp_items.append(f"""
            <div class="item">
                <div class="row">
                    <div><strong>{org}</strong> &mdash; <em>{role}</em></div>
                    <div class="right-align">{dates}</div>
                </div>
                <ul>{b_html}</ul>
            </div>
            """)
        exp_html = "\n".join(exp_items)

        proj_items = []
        for proj in projects:
            title = proj.get("title", "")
            tech_list = proj.get("tech_stack", [])
            tech_str = ", ".join(tech_list) if isinstance(tech_list, list) else str(tech_list)
            repo_url = proj.get("github_url", "")
            live_url = proj.get("live_url", "")

            links = f'<a href="{repo_url}">GitHub</a>'
            if live_url:
                links += f' | <a href="{live_url}">Live Demo</a>'

            bullets = proj.get("bullets", [])[:2]
            b_html = "\n".join(f"<li>{b.get('text', '') if isinstance(b, dict) else str(b)}</li>" for b in bullets)

            proj_items.append(f"""
            <div class="item">
                <div class="row">
                    <div><strong>{title}</strong> | <em>{tech_str}</em></div>
                    <div class="right-align">{links}</div>
                </div>
                <ul>{b_html}</ul>
            </div>
            """)
        proj_html = "\n".join(proj_items)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
    @page {{
        size: letter;
        margin: 0.35in;
    }}
    body {{
        font-family: 'Times New Roman', Times, serif, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.3;
        color: #111;
        margin: 0;
        padding: 0;
    }}
    h1 {{
        text-align: center;
        font-size: 20pt;
        text-transform: uppercase;
        margin: 0 0 2px 0;
        letter-spacing: 1px;
    }}
    .contact {{
        text-align: center;
        font-size: 9pt;
        margin-bottom: 8px;
    }}
    .contact a {{
        color: #111;
        text-decoration: underline;
    }}
    .section-title {{
        font-size: 11pt;
        font-weight: bold;
        text-transform: uppercase;
        border-bottom: 1px solid #111;
        margin-top: 8px;
        margin-bottom: 4px;
        letter-spacing: 0.5px;
    }}
    .row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 2px;
    }}
    .right-align {{
        text-align: right;
        font-style: italic;
    }}
    .item {{
        margin-bottom: 4px;
    }}
    ul {{
        margin: 2px 0 4px 16px;
        padding: 0;
    }}
    li {{
        margin-bottom: 2px;
    }}
    a {{
        color: #111;
        text-decoration: underline;
    }}
</style>
</head>
<body>

<h1>{name}</h1>
<div class="contact">
    {phone} &mdash; <a href="mailto:{email}">{email}</a> &mdash; <a href="{linkedin}">LinkedIn</a> &mdash; <a href="{github}">GitHub</a>
</div>

<div class="section-title">Education</div>
{edu_html}

<div class="section-title">Experience</div>
{exp_html}

<div class="section-title">Projects</div>
{proj_html}

<div class="section-title">Technical Skills</div>
<div style="font-size: 10pt; line-height: 1.4;">
    <strong>Programming Languages:</strong> Python, Java, SQL, JavaScript, HTML/CSS, React, Bash, C/C++<br>
    <strong>AI, ML & LLMs:</strong> Claude API, Gemini API, PyTorch, Scikit-Learn, LightGBM, XGBoost, NLP, TF-IDF, RAG, ChromaDB<br>
    <strong>Backend & APIs:</strong> Flask, REST APIs, FastAPI, PostgreSQL, Redis, Celery, Chrome Extensions<br>
    <strong>Tools & Infrastructure:</strong> Git, GitHub, Docker, LinkedIn Recruiter, Ceipal, Postman, Render, Vercel
</div>

</body>
</html>
"""
        return html_content

    def compile_pdf(self, candidate_data: Dict[str, Any], output_pdf_path: Path) -> bool:
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        html_content = self._generate_print_html(candidate_data)

        temp_html_path = output_pdf_path.parent / "temp_resume_print.html"
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        cmd = [
            self.edge_path,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={str(output_pdf_path)}",
            str(temp_html_path)
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if output_pdf_path.exists() and output_pdf_path.stat().st_size > 1000:
                print(f" [+] PDF compiled successfully at: {output_pdf_path}")
                if temp_html_path.exists():
                    temp_html_path.unlink()
                return True
        except Exception as e:
            print(f"⚠️ PDF compilation notice: {e}")

        return False
