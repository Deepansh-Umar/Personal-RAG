import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import DataIngestionLoader
from src.serializer import CareerChunkSerializer
from src.embedder import SentenceTransformerEmbedder
from src.store import VectorStore
from src.jd_parser import HeuristicJDParser
from src.retriever import HybridRetriever
from src.latex_exporter import LaTeXResumeExporter


def test_latex_export():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    template_path = base_dir / "templates" / "resume_template.tex"
    output_path = base_dir / "output" / "tailored_resume.tex"

    loader = DataIngestionLoader(data_dir)
    career_data = loader.load_all()

    serializer = CareerChunkSerializer()
    chunks = serializer.serialize(career_data)

    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    vector_store = VectorStore(embedder=embedder)
    vector_store.add_chunks(chunks)

    jd_parser = HeuristicJDParser()
    parsed_jd = jd_parser.parse("Looking for Senior RAG Engineer with Python, FastAPI, and Qdrant.")

    retriever = HybridRetriever(vector_store)
    retrieved_chunks = retriever.retrieve_context(parsed_jd, top_k=4)

    exporter = LaTeXResumeExporter(template_path)
    out_file = exporter.export(career_data, retrieved_chunks, output_path)

    print(f"\n[+] Successfully exported tailored LaTeX resume to: {out_file}")
    assert Path(out_file).exists()


if __name__ == "__main__":
    test_latex_export()
