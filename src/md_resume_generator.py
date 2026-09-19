import os
from typing import List, Dict, Any, Optional
from src.jd_parser import ParsedJobDescription
from src.fact_extractor import ProfileFactSheet


class DynamicMarkdownResumeGenerator:
    """
    Pure RAG Markdown Resume Generator.
    Combines:
    1. Tier 1: Fact Sheet (Name, Email, Phone, LinkedIn, GitHub, Date-prioritized Educations).
    2. Tier 2: Vector DB / Full-Context Selected Projects & Experiences (with exact GitHub Repo & Live URLs).
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                print("⚠️ `google-genai` package not found. Running generator in fallback mode.")

    def construct_prompt(
        self,
        parsed_jd: ParsedJobDescription,
        retrieved_context: Dict[str, Any],
        fact_sheet: Optional[ProfileFactSheet] = None
    ) -> str:

        if not fact_sheet:
            fact_sheet = ProfileFactSheet()

        # Format Education Facts string
        edu_lines = []
        if fact_sheet.educations:
            for edu in fact_sheet.educations:
                detail_str = f" ({edu.cgpa_or_details})" if edu.cgpa_or_details else ""
                edu_lines.append(f"- **{edu.institution}** | {edu.dates}  \n  *{edu.degree}*{detail_str}")
        else:
            edu_lines = [
                "- **Indian Institute of Technology Madras** | 2024 – Present  \n  *Bachelor of Science in Data Science and Applications* (CGPA: 9.23 / 10.0)",
                "- **Institute of Aeronautical Engineering, Hyderabad** | 2024 – Present  \n  *Bachelor of Technology in Computer Science and Engineering* (CGPA: 8.6 / 10.0)"
            ]
        education_facts_str = "\n".join(edu_lines)

        # Format Dynamically Selected Projects with exact Repo and Live URLs
        project_blocks = []
        for proj_title, chunks in retrieved_context.get("selected_projects", []):
            sample_meta = chunks[0]["metadata"] if chunks else {}
            repo_url = sample_meta.get("repo_url", fact_sheet.github)
            live_url = sample_meta.get("live_url", "")

            link_str = f"[{proj_title}]({repo_url})"
            if live_url:
                link_str += f" | [Live Demo]({live_url})"

            bullets_text = "\n".join(f"  - {c['content']}" for c in chunks)
            project_blocks.append(f"### {link_str}\n{bullets_text}\n")

        projects_str = "\n".join(project_blocks)

        # Format Experience context
        exp_blocks = [f"- {c['content']}" for c in retrieved_context.get("experience_chunks", [])]
        exp_str = "\n".join(exp_blocks)

        # Handle responsibilities property compatibility
        resps = getattr(parsed_jd, 'core_responsibilities', getattr(parsed_jd, 'key_responsibilities', []))

        prompt = f"""
You are an expert ATS Resume Strategist and Technical Career Coach. 
Your goal is to generate a **Tailored Markdown Resume (.md)** using the candidate's authentic Fact Sheet for Education/Header, and the retrieved projects/accomplishments for experience.

================ CANDIDATE MANDATORY FACT SHEET (TIER 1) ================
Name: {fact_sheet.name or 'Deepansh Umar'}
Contact Line: `{fact_sheet.email or 'umardeepansh@gmail.com'}` | `{fact_sheet.phone or '(+91) 9581730273'}` | [LinkedIn]({fact_sheet.linkedin or 'https://linkedin.com/in/deepansh-umar'}) | [GitHub]({fact_sheet.github or 'https://github.com/Deepansh-Umar'})

Education Facts (MUST BE EXACT):
{education_facts_str}

Experience Facts:
- {fact_sheet.latest_role or 'Student Mentor – e-DAM IARE (Sept 2025 – Present)'}

================ MANDATORY STYLING & SECTION ORDER ================
1. `# {fact_sheet.name or 'Deepansh Umar'}`
   `{fact_sheet.email or 'umardeepansh@gmail.com'}` | `{fact_sheet.phone or '(+91) 9581730273'}` | [LinkedIn]({fact_sheet.linkedin or 'https://linkedin.com/in/deepansh-umar'}) | [GitHub]({fact_sheet.github or 'https://github.com/Deepansh-Umar'})

2. `## EDUCATION`
   {education_facts_str}

3. `## EXPERIENCE`
   - Use retrieved experience context. Start bullet points with strong action verbs.

4. `## PROJECTS`
   - Use ONLY the selected candidate projects below.
   - Preserve exact Markdown Project Header links: `### [Project Name](repo_url) | [Live Demo](live_url)` if live demo URL exists.
   - For each project, write 2 to 3 high-impact STAR bullet points tailored to the target Job Description.

5. `## TECHNICAL SKILLS`
   - Group skills into: `Programming Languages`, `Backend & APIs`, `Frontend`, `Databases`, `Machine Learning`, `Core CS Fundamentals`, `Tools & Platforms`.

6. `## CODING PROFILES`
   - LeetCode & HackerRank profiles.

7. `## CERTIFICATIONS`
   - Harvard CS50, freeCodeCamp, etc.

================ TARGET JOB DESCRIPTION ================
Title: {parsed_jd.title}
Company: {parsed_jd.company}
Required Tech/Skills: {', '.join(parsed_jd.required_skills)}
Key Responsibilities:
{chr(10).join('- ' + r for r in resps)}

================ SELECTED CANDIDATE PROJECTS WITH EXACT URLS (TIER 2) ================
{projects_str}

================ RETRIEVED EXPERIENCES & SKILLS ================
{exp_str}

================ OUTPUT INSTRUCTION ================
Output ONLY the clean, tailored Markdown Resume (.md) inside a ```markdown ... ``` block. Zero hallucinated education dates, zero fake companies, zero broken URLs.
"""
        return prompt

    def generate_markdown_resume(
        self,
        parsed_jd: ParsedJobDescription,
        retrieved_context: Dict[str, Any],
        fact_sheet: Optional[ProfileFactSheet] = None
    ) -> str:
        prompt = self.construct_prompt(parsed_jd, retrieved_context, fact_sheet)

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                return f"⚠️ LLM API Error: {str(e)}\n\n--- Prompt Created ---\n\n{prompt}"
        else:
            return (
                "ℹ️ **Local Demonstration Mode (No GEMINI_API_KEY provided)**\n"
                "Here is the structured prompt constructed for Tier 1 Fact Sheet + Tier 2 Full-Context Selection:\n\n"
                + prompt
            )
