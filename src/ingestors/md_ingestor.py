import re
from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk


class MarkdownIngestor:
    """
    Parses Markdown (.md) documents like project READMEs or notes.
    Splits content by headers (#, ##, ###) and automatically extracts technology tags.
    """

    KNOWN_TECH = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "qdrant", "chromadb", "pgvector", "postgresql", "redis", "celery",
        "aws", "docker", "kubernetes", "microservices", "rag", "llm",
        "websockets", "crdt", "yjs", "ci/cd", "unit testing", "ollama",
        "langchain", "langgraph", "latex", "node.js", "express"
    ]

    def _extract_tech_stack(self, text: str) -> List[str]:
        lowered = text.lower()
        found = []
        for tech in self.KNOWN_TECH:
            if re.search(r'\b' + re.escape(tech) + r'\b', lowered):
                found.append(tech.title() if len(tech) > 3 else tech.upper())
        return list(set(found))

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

        current_header = filename
        current_lines: List[str] = []

        for line in lines:
            if line.startswith("#"):
                # Save previous section if non-empty
                if current_lines:
                    section_text = "\n".join(current_lines).strip()
                    if len(section_text) > 30:
                        tech_stack = self._extract_tech_stack(section_text)
                        chunk_id = f"md_{filename.lower().replace('.', '_')}_{len(chunks)+1}"
                        chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                source_type="project",
                                title=f"{filename} - {current_header}",
                                content=f"Source Document: {filename}\nSection: {current_header}\n\n{section_text}",
                                tech_stack=tech_stack,
                                domain_tags=["markdown", "project_readme"],
                                metadata={"filename": filename, "header": current_header}
                            )
                        )
                    current_lines = []
                current_header = line.lstrip("#").strip()
            else:
                current_lines.append(line)

        # Flush final section
        if current_lines:
            section_text = "\n".join(current_lines).strip()
            if len(section_text) > 30:
                tech_stack = self._extract_tech_stack(section_text)
                chunk_id = f"md_{filename.lower().replace('.', '_')}_{len(chunks)+1}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_type="project",
                        title=f"{filename} - {current_header}",
                        content=f"Source Document: {filename}\nSection: {current_header}\n\n{section_text}",
                        tech_stack=tech_stack,
                        domain_tags=["markdown", "project_readme"],
                        metadata={"filename": filename, "header": current_header}
                    )
                )

        return chunks
