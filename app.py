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
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.schema import CareerData, DocumentChunk
from src.fact_extractor import FactExtractor, ProfileFactSheet, EducationFact
from src.loader import DataIngestionLoader
from src.serializer import CareerChunkSerializer
from src.ingestors.universal_loader import UniversalDocumentLoader
from src.github_fetcher import GitHubProfileIngestor
from src.embedder import SentenceTransformerEmbedder
from src.store import VectorStore
from src.jd_parser import HeuristicJDParser
from src.retriever import HierarchicalRetriever
from src.md_resume_generator import DynamicMarkdownResumeGenerator
from src.ollama_provider import OllamaLLMProvider

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
    .step-header {
        background-color: #1e293b;
        border-left: 4px solid #6366f1;
        padding: 0.8rem 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "indexed" not in st.session_state:
    st.session_state.indexed = False
if "retrieved_chunks" not in st.session_state:
    st.session_state.retrieved_chunks = []
if "markdown_resume" not in st.session_state:
    st.session_state.markdown_resume = ""
if "fact_sheet" not in st.session_state:
    st.session_state.fact_sheet = ProfileFactSheet()


# Sidebar Settings
with st.sidebar:
    st.image("https://img.icons8.com/isometric/96/brain.png", width=64)
    st.title("Settings & Keys")

    api_provider = st.selectbox(
        "LLM Provider",
        ["Google Gemini API", "Local Ollama (qwen2.5-coder:3b)", "Demonstration Mode"]
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
    top_projects = st.slider("Top Projects to Discover", min_value=2, max_value=6, value=4)

    st.markdown("---")
    st.info("💡 **2-Tier Hybrid RAG**: Tier 1 Fact Sheet guarantees 100% factual education/contact accuracy. Tier 2 RAG vector engine dynamically discovers matching GitHub projects.")


# Header
st.markdown('<div class="main-title">Personal Career RAG & Resume Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Hybrid Fact Sheet + Dynamic RAG Vector Engine for ATS Markdown Resumes</div>', unsafe_allow_html=True)


# Main Interface Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Analyze & Generate Resume", "📄 Tailored Markdown Resume", "ℹ️ How It Works"])

with tab1:
    # STEP 1: Mandatory Fact Sheet Setup
    st.markdown('<div class="step-header">📌 Step 1: Candidate Fact Sheet Setup (Mandatory)</div>', unsafe_allow_html=True)

    fact_source = st.radio(
        "Choose how to initialize your Fact Sheet:",
        ["Option A: Upload Existing Resume (Auto-extract latest facts)", "Option B: Link to ResumeBuilder / Portfolio", "Option C: Enter Basic Details Manually"],
        horizontal=True
    )

    fact_sheet = ProfileFactSheet()

    if "Option A" in fact_source:
        uploaded_resume = st.file_uploader("Upload your latest Resume (PDF / MD / YAML)", type=["pdf", "md", "yaml"])
        if uploaded_resume:
            with tempfile.NamedTemporaryFile(suffix=Path(uploaded_resume.name).suffix, delete=False) as tf:
                tf.write(uploaded_resume.getbuffer())
                extractor = FactExtractor()
                fact_sheet = extractor.resolve_recency(tf.name)
                st.success("Successfully extracted latest Candidate Fact Sheet!")

    elif "Option B" in fact_source:
        portfolio_url = st.text_input("Enter Resume Builder / Portfolio URL", placeholder="e.g. https://resumemate.io/user/alex")
        if portfolio_url:
            st.info(f"Will link portfolio: {portfolio_url}")

    elif "Option C" in fact_source:
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Full Name", placeholder="e.g. Alex Johnson")
            email = st.text_input("Email", placeholder="e.g. alex@example.com")
            phone = st.text_input("Phone", placeholder="e.g. (+1) 555-0199")
        with col_b:
            linkedin = st.text_input("LinkedIn URL", placeholder="e.g. https://linkedin.com/in/alexjohnson")
            github = st.text_input("GitHub Profile URL", placeholder="e.g. https://github.com/alexjohnson")

        fact_sheet = ProfileFactSheet(
            name=name, email=email, phone=phone, linkedin=linkedin, github=github
        )

    st.session_state.fact_sheet = fact_sheet

    # Display Active Fact Sheet Summary if populated
    if fact_sheet.name or fact_sheet.email or fact_sheet.educations:
        with st.expander("📋 View Active Fact Sheet (Guaranteed Fact Accuracy)"):
            st.write(f"**Name**: {fact_sheet.name} | **Email**: {fact_sheet.email} | **Phone**: {fact_sheet.phone}")
            for edu in fact_sheet.educations:
                st.write(f"- **{edu.institution}**: {edu.degree} ({edu.dates}) {edu.cgpa_or_details or ''}")

    st.markdown("---")

    # STEP 2: Projects & JD Input
    st.markdown('<div class="step-header">🐙 Step 2: Ingest Projects (GitHub & Documents) + Target Job Description</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        github_url = st.text_input("GitHub Profile URL (Fetches repos & exact live URLs)", placeholder="e.g. https://github.com/username")
        uploaded_project_files = st.file_uploader("Upload additional project READMEs or docs", type=["pdf", "md", "yaml"], accept_multiple_files=True)

    with col2:
        jd_text = st.text_area("Paste Target Job Description (JD)", height=200, placeholder="Paste role requirements, tech stack, and qualifications...")

    st.markdown("---")
    process_btn = st.button("🔥 Generate Tailored Markdown Resume", type="primary", use_container_width=True)

    if process_btn:
        if not jd_text.strip():
            st.warning("Please paste a Job Description before running analysis.")
        else:
            with st.spinner("Executing Tier 1 Fact Sheet + Tier 2 Dynamic Vector Search..."):
                all_chunks = []

                if uploaded_project_files:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        for file in uploaded_project_files:
                            file_path = temp_path / file.name
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())

                        universal_loader = UniversalDocumentLoader()
                        all_chunks.extend(universal_loader.load_directory(temp_path))

                if not all_chunks and not github_url.strip():
                    sample_dir = Path(__file__).parent / "data"
                    if sample_dir.exists():
                        universal_loader = UniversalDocumentLoader()
                        all_chunks.extend(universal_loader.load_directory(sample_dir))

                if github_url.strip():
                    gh_ingestor = GitHubProfileIngestor()
                    gh_chunks = gh_ingestor.ingest_github_profile(github_url)
                    all_chunks.extend(gh_chunks)

                if not all_chunks:
                    st.error("No project chunks found. Please upload project documents or enter a GitHub username.")
                else:
                    embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
                    vector_store = VectorStore(
                        collection_name="app_rag_collection",
                        persist_dir=None,
                        embedder=embedder
                    )
                    vector_store.add_chunks(all_chunks)

                    jd_parser = HeuristicJDParser()
                    parsed_jd = jd_parser.parse(jd_text)

                    retriever = HierarchicalRetriever(vector_store)
                    retrieved_context = retriever.retrieve_resume_context(parsed_jd, top_project_count=top_projects)

                    md_gen = DynamicMarkdownResumeGenerator()
                    prompt = md_gen.construct_prompt(parsed_jd, retrieved_context, fact_sheet=st.session_state.fact_sheet)

                    if api_provider == "Local Ollama (qwen2.5-coder:3b)":
                        ollama = OllamaLLMProvider(model_name="qwen2.5-coder:3b")
                        res_text = ollama.generate(prompt, timeout_sec=180)
                    else:
                        res_text = md_gen.generate_markdown_resume(parsed_jd, retrieved_context, fact_sheet=st.session_state.fact_sheet)

                    st.session_state.retrieved_context = retrieved_context
                    st.session_state.markdown_resume = res_text
                    st.session_state.indexed = True

                    st.rerun()

with tab2:
    if st.session_state.indexed and st.session_state.markdown_resume:
        st.subheader("📄 Tailored Markdown Resume (.md)")
        st.markdown(st.session_state.markdown_resume)

        st.markdown("---")
        st.download_button(
            label="📥 Download Tailored Markdown Resume (.md)",
            data=st.session_state.markdown_resume,
            file_name="tailored_resume.md",
            mime="text/markdown",
            use_container_width=True
        )
    else:
        st.info("👈 Run an analysis in the 'Analyze & Generate Resume' tab to view your tailored Markdown resume.")

with tab3:
    st.subheader("2-Tier Hybrid Architecture")
    st.markdown("""
    - **Tier 1 (Date-Prioritized Fact Sheet)**: Resolves version conflicts by prioritizing your latest resume data for Education, Degrees, CGPA, and Contact info.
    - **Tier 2 (RAG Vector Engine)**: Dynamically searches GitHub repositories and PDF documents to discover matching projects, extracting exact Repo & Live Hosted URLs.
    """)
