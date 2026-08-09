from pathlib import Path
from typing import List, Dict, Any
from src.schema import CareerData


class LaTeXResumeExporter:
    """
    Renders structured career data and RAG-tailored bullets into a compile-ready LaTeX document.
    """

    def __init__(self, template_path: Path):
        self.template_path = Path(template_path)

    def export(
        self,
        career_data: CareerData,
        retrieved_chunks: List[Dict[str, Any]],
        output_path: Path
    ) -> str:
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template not found at {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            template = f.read()

        profile = career_data.profile
        name = profile.name if profile else "Your Name"
        title = profile.title if profile else "Software Engineer"
        email = profile.email if profile else "email@example.com"
        location = profile.location if profile else "City, Country"
        summary = profile.summary if profile else ""

        # Format Experiences Block using top relevant retrieved chunks
        exp_lines = []
        for chunk in retrieved_chunks:
            if chunk["metadata"].get("source_type") == "experience":
                role_title = chunk["metadata"].get("title", "Software Engineer")
                dates = chunk["metadata"].get("dates", "")
                exp_lines.append(f"  \\item \\textbf{{{role_title}}} \\hfill {{ {dates} }}\\\\")
                # Format bullet point
                content_clean = chunk["content"].replace("%", "\\%").replace("&", "\\&")
                bullet_str = content_clean.split("\n")[1] if "\n" in content_clean else content_clean
                exp_lines.append(f"  \\begin{{itemize}}[leftmargin=0.2in]\n    \\item {bullet_str}\n  \\end{{itemize}}")

        experiences_block = "\n".join(exp_lines)

        # Format Projects Block
        proj_lines = []
        for proj in career_data.projects:
            tech_str = ", ".join(proj.tech_stack)
            proj_lines.append(
                f"  \\item \\textbf{{{proj.name}}} -- \\textit{{{proj.tagline}}} \\hfill \\textbf{{Tech: {tech_str}}}\\\\"
            )
            if proj.key_achievements:
                proj_lines.append("  \\begin{itemize}[leftmargin=0.2in]")
                for ach in proj.key_achievements[:2]:
                    ach_clean = ach.replace("%", "\\%").replace("&", "\\&")
                    proj_lines.append(f"    \\item {ach_clean}")
                proj_lines.append("  \\end{itemize}")

        projects_block = "\n".join(proj_lines)

        # Format Skills Block
        skills_lines = []
        for cat in career_data.skill_categories:
            skill_names = ", ".join([s.name for s in cat.skills])
            skills_lines.append(f"  \\item \\textbf{{{cat.category}}}: {skill_names}")
        skills_block = "\n".join(skills_lines)

        # Perform template substitution
        rendered = template.replace("{{ NAME }}", name)
        rendered = rendered.replace("{{ TITLE }}", title)
        rendered = rendered.replace("{{ EMAIL }}", email)
        rendered = rendered.replace("{{ LOCATION }}", location)
        rendered = rendered.replace("{{ SUMMARY }}", summary)
        rendered = rendered.replace("{{ EXPERIENCES_BLOCK }}", experiences_block)
        rendered = rendered.replace("{{ PROJECTS_BLOCK }}", projects_block)
        rendered = rendered.replace("{{ SKILLS_BLOCK }}", skills_block)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        return str(output_path)
