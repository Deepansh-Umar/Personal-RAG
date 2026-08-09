import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestors.universal_loader import UniversalDocumentLoader
from src.embedder import SentenceTransformerEmbedder
from src.store import VectorStore
from src.langgraph_rag import LangGraphCareerAgent
from src.ollama_provider import OllamaLLMProvider


def test_universal_ingestion_and_langgraph():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"

    print("\n1. Testing Universal Document Ingestion (YAML, Markdown, LaTeX, PDF)...")
    loader = UniversalDocumentLoader()
    chunks = loader.load_directory(data_dir)

    print(f" [+] Total Multi-Format Chunks Loaded: {len(chunks)}")
    for c in chunks[:4]:
        print(f"     -> Chunk ID: {c.chunk_id} | Title: {c.title}")
        print(f"        Tech Tags: {c.tech_stack}")

    print("\n2. Indexing into Vector Store...")
    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    vector_store = VectorStore(collection_name="universal_chunks", embedder=embedder)
    vector_store.add_chunks(chunks)

    print("\n3. Testing Ollama Local LLM Connectivity...")
    ollama = OllamaLLMProvider()
    if ollama.is_available():
        print(" [+] Ollama server detected at http://localhost:11434!")
    else:
        print(" [i] Ollama server not active locally (will fall back gracefully).")

    print("\n4. Executing LangGraph Agentic RAG Flow...")
    agent = LangGraphCareerAgent(vector_store)
    sample_jd = """
    We are hiring a Lead AI Engineer proficient in Python, FastAPI, React, Docker, and Vector Databases (Qdrant/ChromaDB).
    You will lead a team of 4 engineers and optimize microservice latency.
    """
    final_state = agent.execute(sample_jd)

    print(f"\n [+] LangGraph Completed with final relevance score: {final_state['relevance_score']}")
    assert len(final_state["retrieved_chunks"]) > 0


if __name__ == "__main__":
    test_universal_ingestion_and_langgraph()
