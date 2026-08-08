import re
from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk


class LaTeXIngestor:
    r"""
    Parses LaTeX (.tex) resume documents and structural templates.
    Strips raw LaTeX commands, extracts section blocks (\section{...}),
    and converts text into DocumentChunks.
    """

    KNOWN_TECH = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "qdrant", "chromadb", "pgvector", "postgresql", "redis", "celery",
        "aws", "docker", "kubernetes", "microservices", "rag", "llm",
        "websockets", "crdt", "latex", "sql"
    ]

    def _clean_latex_markup(self, text: str) -> str:
        # Strip comments
        text = re.sub(r'%.*', '', text)
        # Strip common formatting commands
        text = re.sub(r'\\textbf\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\\textit\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\\href\{[^}]+\}\{([^}]+)\}', r'\1', text)
        text = re.sub(r'\\item\s*', '- ', text)
        text = re.sub(r'\\hfill\s*', ' | ', text)
        text = re.sub(r'\\begin\{[^}]+\}', '', text)
        text = re.sub(r'\\end\{[^}]+\}', '', text)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        text = re.sub(r'[{}]', '', text)
        return re.sub(r'\n\s*\n', '\n', text).strip()

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
            raise FileNotFoundError(f"LaTeX file not found: {path}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw_latex = f.read()

        return self.parse_text(raw_latex, filename=path.name)

    def parse_text(self, latex_text: str, filename: str = "resume.tex") -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        sections = re.split(r'\\section\{([^}]+)\}', latex_text)

        if len(sections) > 1:
            for i in range(1, len(sections), 2):
                section_title = sections[i].strip()
                raw_body = sections[i+1] if i+1 < len(sections) else ""
                clean_body = self._clean_latex_markup(raw_body)

                if len(clean_body) > 20:
                    tech_stack = self._extract_tech(clean_body)
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"tex_{filename.lower().replace('.', '_')}_sec_{i//2+1}",
                            source_type="experience" if "experience" in section_title.lower() else "project",
                            title=f"{filename} - Section: {section_title}",
                            content=f"Document: {filename}\nSection: {section_title}\n\n{clean_body}",
                            tech_stack=tech_stack,
                            domain_tags=["latex", "resume_tex"],
                            metadata={"filename": filename, "section": section_title}
                        )
                    )
        else:
            clean_body = self._clean_latex_markup(latex_text)
            if len(clean_body) > 20:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"tex_{filename.lower().replace('.', '_')}_full",
                        source_type="experience",
                        title=f"LaTeX Document: {filename}",
                        content=clean_body,
                        tech_stack=self._extract_tech(clean_body),
                        domain_tags=["latex"],
                        metadata={"filename": filename}
                    )
                )

        return chunks
