import re
from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk


class MarkdownIngestor:
    """
    Parses Markdown (.md) project READMEs into clean, high-signal DocumentChunks.
    Filters out boilerplate sections (Installation, Setup, License) to focus purely
    on Features, Architecture, Tech Stack, and Technical Achievements.
    """

    KNOWN_TECH = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "qdrant", "chromadb", "pgvector", "postgresql", "redis", "celery",
        "aws", "docker", "kubernetes", "microservices", "rag", "llm",
        "websockets", "crdt", "yjs", "ci/cd", "unit testing", "ollama",
        "langchain", "langgraph", "latex", "node.js", "express", "pytorch",
        "tensorflow", "scikit-learn", "pandas", "numpy", "html", "css", "git"
    ]

    NOISE_SECTIONS = [
        "installation", "install", "local setup", "how to run", "getting started",
        "prerequisites", "requirements", "license", "contributing", "author",
        "table of contents", "toc"
    ]

    def _extract_tech_stack(self, text: str) -> List[str]:
        lowered = text.lower()
        found = []
        for tech in self.KNOWN_TECH:
            if re.search(r'\b' + re.escape(tech) + r'\b', lowered):
                found.append(tech.title() if len(tech) > 3 else tech.upper())
        return list(set(found))

    def _is_noise_header(self, header_title: str) -> bool:
        lowered = header_title.lower().strip()
        return any(noise in lowered for noise in self.NOISE_SECTIONS)

    def _clean_project_name(self, filename: str) -> str:
        name = filename.replace("GitHub_", "").replace("_README.md", "").replace(".md", "")
        return name.replace("_", " ").strip()

    def parse_file(self, file_path: Union[str, Path]) -> List[DocumentChunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {path}")

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return self.parse_text(content, filename=path.name)

    def parse_text(self, markdown_text: str, filename: str = "README.md") -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        lines = markdown_text.split("\n")

        clean_repo_name = self._clean_project_name(filename)
        current_header = clean_repo_name
        current_lines: List[str] = []

        for line in lines:
            if line.startswith("#"):
                if current_lines:
                    section_text = "\n".join(current_lines).strip()
                    if len(section_text) > 40 and not self._is_noise_header(current_header):
                        tech_stack = self._extract_tech_stack(section_text)
                        chunk_id = f"md_{clean_repo_name.lower().replace(' ', '_')}_{len(chunks)+1}"
                        chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                source_type="project",
                                title=f"{clean_repo_name} ({current_header})",
                                content=f"Project Name: {clean_repo_name}\nSection: {current_header}\n\n{section_text}",
                                tech_stack=tech_stack,
                                domain_tags=["markdown", "project_readme", clean_repo_name.lower()],
                                metadata={"filename": filename, "repo_name": clean_repo_name, "header": current_header}
                            )
                        )
                    current_lines = []
                current_header = line.lstrip("#").strip()
            else:
                current_lines.append(line)

        if current_lines:
            section_text = "\n".join(current_lines).strip()
            if len(section_text) > 40 and not self._is_noise_header(current_header):
                tech_stack = self._extract_tech_stack(section_text)
                chunk_id = f"md_{clean_repo_name.lower().replace(' ', '_')}_{len(chunks)+1}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_type="project",
                        title=f"{clean_repo_name} ({current_header})",
                        content=f"Project Name: {clean_repo_name}\nSection: {current_header}\n\n{section_text}",
                        tech_stack=tech_stack,
                        domain_tags=["markdown", "project_readme", clean_repo_name.lower()],
                        metadata={"filename": filename, "repo_name": clean_repo_name, "header": current_header}
                    )
                )

        return chunks
