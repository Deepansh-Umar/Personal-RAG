import os
import sys
from pathlib import Path

# Configure utf-8 encoding for stdout on Windows terminals
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestors.universal_loader import UniversalDocumentLoader
from src.embedder import SentenceTransformerEmbedder
from src.store import VectorStore
from src.jd_parser import HeuristicJDParser
from src.retriever import HybridRetriever
from src.generator import CareerRAGGenerator
from src.langgraph_rag import LangGraphCareerAgent


# Sample Job Description for Testing
SAMPLE_JD = """
Company: AI Scale Systems
Role: Senior RAG & AI Platform Engineer

We are seeking a Senior AI Platform Engineer to build next-generation enterprise RAG systems.
In this role, you will design microservices, optimize vector search latency, and integrate hybrid search (Qdrant/ChromaDB).

Key Responsibilities:
- Architect scalable RAG pipelines handling 10k+ requests per minute with low latency.
- Build high-performance backend microservices using FastAPI, Python, and AWS ECS.
- Optimize vector similarity search accuracy using custom embeddings, reranking, and metadata filtering.
- Mentor junior software engineers and champion unit testing and CI/CD best practices.

Requirements:
- 4+ years software engineering experience in Python, FastAPI, Docker, and Microservices.
- Hands-on experience with Vector Databases (Qdrant, ChromaDB, pgvector) and RAG architecture.
- Demonstrated track record of optimizing system response latency and SQL/NoSQL performance.
"""


def run_pipeline(jd_text: str = SAMPLE_JD, use_langgraph: bool = True):
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    db_dir = base_dir / "chroma_db"

    print("\n[+] Starting Personal Career RAG Pipeline...")
    print("=" * 60)

    # Step 1: Universal Document Ingestion (YAML, Markdown READMEs, LaTeX, PDF)
    print("\n[Step 1] Ingesting Personal Documents (YAML, Markdown READMEs, LaTeX, PDFs)...")
    loader = UniversalDocumentLoader()
    chunks = loader.load_directory(data_dir)
    print(f" -> Generated {len(chunks)} multi-format searchable document chunks.")

    # Step 2: Embed & Store in Vector DB
    print("\n[Step 2] Initializing local vector store (ChromaDB + SentenceTransformers)...")
    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
    vector_store = VectorStore(
        collection_name="universal_career_collection",
        persist_dir=str(db_dir),
        embedder=embedder
    )
    vector_store.add_chunks(chunks)
    print(" -> Indexed all multi-format chunks into local ChromaDB!")

    if use_langgraph:
        print("\n[Step 3] Running LangGraph Agentic RAG Pipeline (With State & Self-Correction)...")
        agent = LangGraphCareerAgent(vector_store)
        state = agent.execute(jd_text)
        result = state["final_output"]
    else:
        # Step 3: Parse Target Job Description
        print("\n[Step 3] Analyzing Target Job Description...")
        jd_parser = HeuristicJDParser()
        parsed_jd = jd_parser.parse(jd_text, title="Senior RAG & AI Platform Engineer", company="AI Scale Systems")

        # Step 4: Hybrid Retrieval
        print("\n[Step 4] Performing Hybrid Vector Search...")
        retriever = HybridRetriever(vector_store)
        retrieved_chunks = retriever.retrieve_context(parsed_jd, top_k=5)

        # Step 5: Synthesis Engine
        print("\n[Step 5] Synthesizing Tailored Resume Content...")
        generator = CareerRAGGenerator()
        result = generator.generate_tailored_content(parsed_jd, retrieved_chunks)

    print("\n" + "=" * 60)
    print("RAG TAILORED RESUME OUTPUT & ANALYSIS")
    print("=" * 60 + "\n")
    print(result)


if __name__ == "__main__":
    run_pipeline()
