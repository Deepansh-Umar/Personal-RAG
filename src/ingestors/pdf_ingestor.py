import re
from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk


class PDFIngestor:
    """
    Parses PDF (.pdf) documents (e.g. resumes, certificates, project docs).
    Extracts text page-by-page or by paragraph blocks and auto-tags technologies.
    """

    KNOWN_TECH = [
        "python", "typescript", "javascript", "react", "fastapi", "django",
        "qdrant", "chromadb", "pgvector", "postgresql", "redis", "celery",
        "aws", "docker", "kubernetes", "microservices", "rag", "llm",
        "websockets", "crdt", "latex", "sql"
    ]

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
            # Simple text fallback if pypdf is not yet installed
            print("⚠️ pypdf package not installed. Install via `pip install pypdf` for PDF parsing.")
            return []

        chunks: List[DocumentChunk] = []
        reader = pypdf.PdfReader(str(path))

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            if text and len(text.strip()) > 30:
                clean_text = re.sub(r'\n\s*\n', '\n', text).strip()
                tech_stack = self._extract_tech(clean_text)

                chunks.append(
                    DocumentChunk(
                        chunk_id=f"pdf_{path.name.lower().replace('.', '_')}_p{page_num}",
                        source_type="experience",
                        title=f"PDF Document: {path.name} (Page {page_num})",
                        content=f"Document: {path.name} (Page {page_num})\n\n{clean_text}",
                        tech_stack=tech_stack,
                        domain_tags=["pdf", "resume_pdf"],
                        metadata={"filename": path.name, "page": page_num}
                    )
                )

        return chunks
