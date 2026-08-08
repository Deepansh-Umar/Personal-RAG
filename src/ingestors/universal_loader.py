from pathlib import Path
from typing import List, Union
from src.schema import DocumentChunk
from src.loader import DataIngestionLoader
from src.serializer import CareerChunkSerializer
from src.ingestors.md_ingestor import MarkdownIngestor
from src.ingestors.tex_ingestor import LaTeXIngestor
from src.ingestors.pdf_ingestor import PDFIngestor


class UniversalDocumentLoader:
    """
    Universal Ingestion Loader for Personal RAG.
    Supports parsing YAML data, Markdown READMEs (.md), LaTeX templates (.tex), and PDFs (.pdf).
    """

    def __init__(self):
        self.md_ingestor = MarkdownIngestor()
        self.tex_ingestor = LaTeXIngestor()
        self.pdf_ingestor = PDFIngestor()
        self.yaml_serializer = CareerChunkSerializer()

    def load_directory(self, data_dir: Union[str, Path]) -> List[DocumentChunk]:
        path = Path(data_dir)
        all_chunks: List[DocumentChunk] = []

        if not path.exists():
            return all_chunks

        # 1. Load structured YAML files if present
        yaml_loader = DataIngestionLoader(path)
        career_data = yaml_loader.load_all()
        yaml_chunks = self.yaml_serializer.serialize(career_data)
        all_chunks.extend(yaml_chunks)

        # 2. Ingest Markdown READMEs and .md files
        for md_file in path.rglob("*.md"):
            try:
                chunks = self.md_ingestor.parse_file(md_file)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Error parsing Markdown file {md_file.name}: {e}")

        # 3. Ingest LaTeX documents (.tex)
        for tex_file in path.rglob("*.tex"):
            try:
                chunks = self.tex_ingestor.parse_file(tex_file)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Error parsing LaTeX file {tex_file.name}: {e}")

        # 4. Ingest PDF documents (.pdf)
        for pdf_file in path.rglob("*.pdf"):
            try:
                chunks = self.pdf_ingestor.parse_file(pdf_file)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"⚠️ Error parsing PDF file {pdf_file.name}: {e}")

        return all_chunks
