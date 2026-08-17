import os
import sys
import tempfile
from pathlib import Path
import streamlit as st

# Configure page layout & title
st.set_page_config(
    page_title="Personal Career RAG & Resume Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.schema import CareerData, DocumentChunk
from src.loader import DataIngestionLoader
from src.serializer import CareerChunkSerializer
from src.ingestors.universal_loader import UniversalDocumentLoader
from src.github_fetcher import GitHubProfileIngestor
from src.embedder import SentenceTransformerEmbedder
from src.store import VectorStore
from src.jd_parser import HeuristicJDParser
from src.retriever import HybridRetriever
from src.generator import CareerRAGGenerator
from src.langgraph_rag import LangGraphCareerAgent
from src.latex_exporter import LaTeXResumeExporter

# Custom CSS styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "indexed" not in st.session_state:
    st.session_state.indexed = False
if "retrieved_chunks" not in st.session_state:
    st.session_state.retrieved_chunks = []
if "rag_output" not in st.session_state:
    st.session_state.rag_output = ""
if "latex_content" not in st.session_state:
    st.session_state.latex_content = ""


# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/brain.png", width=64)
    st.title("Settings & Keys")

    api_provider = st.selectbox(
        "LLM Provider",
        ["Google Gemini API", "Local Ollama (100% Private)", "Demonstration Mode"]
    )

    gemini_key = ""
    if api_provider == "Google Gemini API":
        gemini_key = st.text_input(
            "Enter Gemini API Key",
            type="password",
            help="Your API key is used strictly in session and never saved."
        )
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key

    st.markdown("---")
    st.subheader("RAG Parameters")
    top_k = st.slider("Top-K Retrieved Context Chunks", min_value=2, max_value=8, value=5)
    use_langgraph = st.checkbox("Enable LangGraph Agentic Loops", value=True)

    st.markdown("---")
    st.info("💡 **Hosted Version Note**: End-users can upload personal career documents and enter their API key. Data is processed ephemerally in memory.")


# App Header
st.markdown('<div class="main-title">Personal Career RAG & Resume Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-Powered Career Document Matching, JD Analysis & ATS Resume Generator</div>', unsafe_allow_html=True)


# Main Interface Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Analyze & Match", "📄 Resume & LaTeX Output", "ℹ️ How It Works"])

with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1️⃣ Upload Personal Career Documents")

        # Option A: File Upload
        uploaded_files = st.file_uploader(
            "Upload Resumes, Projects, READMEs, PDFs, or YAML",
            type=["pdf", "md", "tex", "yaml", "yml"],
            accept_multiple_files=True
        )

        # Option B: GitHub Import
        st.markdown("**OR Import From GitHub**")
        github_url = st.text_input("GitHub Username or Profile URL", placeholder="https://github.com/Deepansh-Umar")

        fetch_github = st.button("🐙 Fetch GitHub Repos & READMEs", use_container_width=True)

    with col2:
        st.subheader("2️⃣ Target Job Description (JD)")
        jd_text = st.text_area(
            "Paste the Job Description here",
            height=260,
            placeholder="Paste role responsibilities, tech stack requirements, and qualifications..."
        )

    st.markdown("---")
    process_btn = st.button("🔥 Run Career RAG Analysis", type="primary", use_container_width=True)

    if process_btn:
        if not jd_text.strip():
            st.warning("Please paste a Job Description before running analysis.")
        else:
            with st.spinner("Ingesting documents, indexing vector store, and running RAG pipeline..."):
                all_chunks = []

                # Ingest uploaded files
                if uploaded_files:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        for file in uploaded_files:
                            file_path = temp_path / file.name
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())

                        universal_loader = UniversalDocumentLoader()
                        all_chunks.extend(universal_loader.load_directory(temp_path))

                # Ingest local sample data if no files uploaded
                if not all_chunks and not fetch_github:
                    sample_dir = Path(__file__).parent / "data"
                    if sample_dir.exists():
                        universal_loader = UniversalDocumentLoader()
                        all_chunks.extend(universal_loader.load_directory(sample_dir))

                # Ingest GitHub if specified
                if github_url.strip():
                    gh_ingestor = GitHubProfileIngestor()
                    gh_chunks = gh_ingestor.ingest_github_profile(github_url)
                    all_chunks.extend(gh_chunks)

                if not all_chunks:
                    st.error("No valid document chunks found. Please upload documents or enter a valid GitHub username.")
                else:
                    st.success(f"Successfully processed {len(all_chunks)} searchable career chunks!")

                    # Vector Indexing
                    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
                    vector_store = VectorStore(
                        collection_name="streamlit_career_chunks",
                        persist_dir=None,
                        embedder=embedder
                    )
                    vector_store.add_chunks(all_chunks)

                    # Retrieval & Synthesis
                    if use_langgraph:
                        agent = LangGraphCareerAgent(vector_store)
                        state = agent.execute(jd_text)
                        retrieved = state["retrieved_chunks"]
                        output = state["final_output"]
                    else:
                        jd_parser = HeuristicJDParser()
                        parsed_jd = jd_parser.parse(jd_text)
                        retriever = HybridRetriever(vector_store)
                        retrieved = retriever.retrieve_context(parsed_jd, top_k=top_k)
                        generator = CareerRAGGenerator()
                        output = generator.generate_tailored_content(parsed_jd, retrieved)

                    st.session_state.retrieved_chunks = retrieved
                    st.session_state.rag_output = output
                    st.session_state.indexed = True

                    # Generate LaTeX Output
                    try:
                        template_path = Path(__file__).parent / "templates" / "resume_template.tex"
                        if template_path.exists():
                            loader = DataIngestionLoader(Path(__file__).parent / "data")
                            career_data = loader.load_all()
                            exporter = LaTeXResumeExporter(template_path)
                            with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as tf:
                                exporter.export(career_data, retrieved, Path(tf.name))
                                with open(tf.name, "r", encoding="utf-8") as f:
                                    st.session_state.latex_content = f.read()
                    except Exception as e:
                        st.session_state.latex_content = f"% Error generating LaTeX: {e}"

                    st.rerun()

with tab2:
    if st.session_state.indexed and st.session_state.rag_output:
        st.subheader("📋 RAG Analysis & ATS Bullet Recommendations")
        st.markdown(st.session_state.rag_output)

        st.markdown("---")
        st.subheader("🔍 Top Retrieved Context Chunks")
        for idx, chunk in enumerate(st.session_state.retrieved_chunks, 1):
            with st.expander(f"Chunk #{idx}: {chunk['metadata'].get('title', 'N/A')} (Similarity Score: {chunk['similarity_score']})"):
                st.markdown(f"**Source Type**: `{chunk['metadata'].get('source_type', 'N/A')}`")
                st.markdown(f"**Tech Stack**: `{chunk['metadata'].get('tech_stack', 'N/A')}`")
                st.text(chunk["content"])

        if st.session_state.latex_content:
            st.markdown("---")
            st.subheader("📄 Tailored LaTeX Resume Code")
            st.code(st.session_state.latex_content, language="latex")
            st.download_button(
                label="📥 Download Tailored LaTeX Resume (.tex)",
                data=st.session_state.latex_content,
                file_name="tailored_resume.tex",
                mime="text/x-tex",
                use_container_width=True
            )
    else:
        st.info("👈 Please run an analysis in the 'Analyze & Match' tab to view tailored resume recommendations and LaTeX outputs.")

with tab3:
    st.subheader("Architecture & How It Works")
    st.markdown("""
    ### 🏗️ System Architecture

    1. **Multi-Format Ingestion Engine**:
       - Converts Markdown READMEs (`.md`), PDFs (`.pdf`), LaTeX resumes (`.tex`), and YAML (`.yaml`) into metadata-enriched chunks.
       - Can pull public repository READMEs directly via the **GitHub REST API**.

    2. **Local Vector Store & Embeddings**:
       - Powered by **ChromaDB** and HuggingFace **SentenceTransformers (`all-MiniLM-L6-v2`)**.
       - Calculates 384-dimensional cosine similarity embeddings in memory.

    3. **Hybrid Retriever**:
       - Combines dense semantic vector search with technology tag boosting to ensure mandatory JD skills match.

    4. **LangGraph Agentic Workflow**:
       - Runs stateful agent nodes: `Parse JD -> Retrieve Chunks -> Grade Relevance -> Self-Correction Loop -> LLM Synthesis`.
    """)
