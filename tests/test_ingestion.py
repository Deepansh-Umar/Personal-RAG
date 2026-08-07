import sys
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.loader import DataIngestionLoader
from src.serializer import CareerChunkSerializer


def test_ingestion_and_serialization():
    data_dir = Path(__file__).parent.parent / "data"
    
    # 1. Test loader
    loader = DataIngestionLoader(data_dir)
    career_data = loader.load_all()
    
    assert career_data.profile is not None
    assert career_data.profile.name == "Alex Dev"
    assert len(career_data.experiences) > 0
    assert len(career_data.projects) > 0
    assert len(career_data.skill_categories) > 0
    assert len(career_data.strengths) > 0
    
    # 2. Test serializer
    serializer = CareerChunkSerializer()
    chunks = serializer.serialize(career_data)
    
    assert len(chunks) > 0
    
    print(f"\n Successfully loaded and serialized {len(chunks)} chunks!")
    print("\n--- Sample Serialized Chunks ---")
    for chunk in chunks[:3]:
        print(f"ID: {chunk.chunk_id} | Type: {chunk.source_type} | Title: {chunk.title}")
        print(f"Tech Stack: {chunk.tech_stack}")
        print(f"Content:\n{chunk.content}\n" + "-"*40)


if __name__ == "__main__":
    test_ingestion_and_serialization()
