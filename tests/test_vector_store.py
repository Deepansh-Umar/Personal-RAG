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


def test_vector_store_indexing_and_search():
    data_dir = Path(__file__).parent.parent / "data"
    db_dir = Path(__file__).parent.parent / "chroma_db_test"

    print("1. Loading career data...")
    loader = DataIngestionLoader(data_dir)
    career_data = loader.load_all()

    print("2. Serializing into DocumentChunks...")
    serializer = CareerChunkSerializer()
    chunks = serializer.serialize(career_data)

    print("3. Initializing SentenceTransformerEmbedder (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")

    print("4. Indexing into ChromaDB Vector Store...")
    vector_store = VectorStore(
        collection_name="test_career_chunks",
        persist_dir=str(db_dir),
        embedder=embedder
    )
    vector_store.add_chunks(chunks)
    print(f" Successfully indexed {len(chunks)} chunks!")

    # Test Queries
    test_queries = [
        "FastAPI microservices and latency optimization",
        "RAG system vector database Qdrant",
        "Collaborative WebSockets and React frontend project",
        "Leadership mentoring unit testing CI/CD"
    ]

    print("\n================ SEARCH VERIFICATION ================")
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = vector_store.search(query=query, top_k=2)
        for idx, res in enumerate(results, 1):
            print(f"  [{idx}] Score: {res['similarity_score']} | ID: {res['chunk_id']}")
            print(f"      Title: {res['metadata'].get('title')}")
            print(f"      Content Snippet: {res['content'][:120]}...")

    print("\n Vector Store Test Completed Successfully!")


if __name__ == "__main__":
    test_vector_store_indexing_and_search()
