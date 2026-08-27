import re
from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk


class PDFIngestor:
    """
    Parses PDF (.pdf) resume documents by splitting on major section headers
    (EXPERIENCE, PROJECTS, EDUCATION, SKILLS) and individual bullet points.
    Prevents vector dilution and maximizes RAG retrieval precision.
    """

    KNOWN_TECH = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "flask", "vue.js", "sqlalchemy", "qdrant", "chromadb", "pgvector",
        "postgresql", "redis", "celery", "aws", "docker", "kubernetes",
        "microservices", "rag", "llm", "websockets", "crdt", "latex", "sql",
        "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy", "html",
        "css", "git", "jwt", "rest apis"
    ]

    SECTIONS = ["EXPERIENCE", "PROJECTS", "EDUCATION", "SKILLS", "CERTIFICATIONS", "KEY HIGHLIGHTS"]

    def _extract_tech(self, text: str) -> List[str]:
        lowered = text.lower()
        found = []
        for tech in self.KNOWN_TECH:
            if re.search(r'\b' + re.escape(tech) + r'\b', lowered):
                found.append(tech.title() if len(tech) > 3 else tech.upper())
        return list(set(found))

    def parse_file(self, file_path: Union[str, Path]) -> List[DocumentChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        try:
            import pypdf
        except ImportError:
            print("⚠️ pypdf package not installed. Install via `pip install pypdf` for PDF parsing.")
            return []

        chunks: List[DocumentChunk] = []
        reader = pypdf.PdfReader(str(path))

        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        if not full_text.strip():
            return chunks

        # 1. Split into Major Sections (EXPERIENCE, PROJECTS, EDUCATION, SKILLS)
        pattern = r'(?=\b(?:' + '|'.join(self.SECTIONS) + r')\b)'
        section_blocks = re.split(pattern, full_text)

        for block in section_blocks:
            clean_block = block.strip()
            if len(clean_block) < 30:
                continue

            # Identify section name
            first_line = clean_block.split("\n")[0].upper()
            matched_section = "GENERAL"
            for sec in self.SECTIONS:
                if sec in first_line:
                    matched_section = sec
                    break

            # 2. Split section into sub-bullets (by bullet symbols '', '•', '-', '*')
            bullets = re.split(r'[\ufffd\u2022\u25cf\u25aa\u25b6\*\-]\s*', clean_block)

            for b_idx, bullet in enumerate(bullets, 1):
                clean_bullet = re.sub(r'\s+', ' ', bullet).strip()

                # Filter out short lines or contact headers
                if len(clean_bullet) < 35 or re.match(r'^(email|phone|linkedin|github|\(\+[\d\s-]+\))', clean_bullet.lower()):
                    continue

                tech_stack = self._extract_tech(clean_bullet)
                chunk_id = f"pdf_{path.name.lower().replace('.', '_')}_{matched_section.lower()}_{b_idx}"

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_type="project" if matched_section == "PROJECTS" else "experience",
                        title=f"{path.name} - {matched_section} (Bullet {b_idx})",
                        content=f"Document: {path.name}\nSection: {matched_section}\nAccomplishment: {clean_bullet}",
                        tech_stack=tech_stack,
                        domain_tags=["pdf", matched_section.lower()],
                        metadata={"filename": path.name, "section": matched_section}
                    )
                )

        return chunks
