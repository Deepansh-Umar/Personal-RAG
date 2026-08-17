# Personal Career RAG and Agentic Assistant

A modular, local-first Retrieval-Augmented Generation (RAG) pipeline designed to ingest personal career documents (Markdown READMEs, LaTeX files, PDFs, and YAML) and tailor them against specific Job Descriptions (JDs).

Includes support for Local LLMs via Ollama, Google Gemini API, ChromaDB Vector Store, LangGraph Agentic Workflows, and a Streamlit Web Application interface.

---

## System Architecture

```
                                  [Multi-Format Ingestion Suite]
                                 +-------------------------------+
                                 | - Markdown READMEs (.md)      |
                                 | - LaTeX Resumes (.tex)        |
                                 | - PDF Documents (.pdf)        |
                                 | - Structured YAML (.yaml)     |
                                 | - GitHub Profile READMEs      |
                                 +---------------+---------------+
                                                 |
                                                 v
                                     [Universal Document Loader]
                                                 |
                                                 v
                                   [ChromaDB / Qdrant Vector Store]
                                                 |
[Target Job Description] ---> [JD Parser] -------+---> [Hybrid Vector & Skill Tag Retriever]
                                                 |
                                                 v
                                   [LangGraph Agentic State Flow]
                                  (JD Parse -> Retrieve -> Grade -> Self-Correct Loop)
                                                 |
                                                 v
                                    [LLM Synthesis Engine]
                                (Gemini API / Local Ollama LLM)
                                                 |
                                                 v
                                [Tailored Resumes & LaTeX Export]
```

---

## Key Features Explained

### 1. Universal Multi-Format Document Ingestion (`src/ingestors/`)
You can drop any of the following files into the `data/` folder:
- **Markdown READMEs (`.md`)**: Automatically splits project READMEs by headers (`#`, `##`) and auto-extracts technology tags.
- **LaTeX Files (`.tex`)**: Parses LaTeX resume templates or past LaTeX documents into section blocks.
- **PDF Documents (`.pdf`)**: Extracts text page-by-page.
- **Structured YAML (`.yaml`)**: Stores structured STAR bullet points (Situation, Action, Result) linked to companies and tech tags.
- **GitHub Repositories**: Automatically fetches public project READMEs from any GitHub profile URL.

### 2. Streamlit Web Application Interface (`app.py`)
Launch the interactive web user interface locally or deploy to **Streamlit Community Cloud** with 1 click:
```bash
streamlit run app.py
```

### 3. Local LLMs via Ollama & Gemini API (`src/ollama_provider.py`, `src/generator.py`)
Run private open-weight models (`llama3.2`, `qwen2.5`, `deepseek-r1`) locally via Ollama, or enter your Gemini API key in the web interface for sub-second cloud synthesis.

### 4. LangGraph Agentic RAG and Self-Correction (`src/langgraph_rag.py`)
Rather than relying on a linear pipeline, the system uses a LangGraph State Graph:
1. **Analyze JD**: Extracts role title and required skills.
2. **Retrieve Context**: Queries vector store.
3. **Grade Relevance**: Evaluates whether retrieved context answers the JD requirements.
4. **Self-Correction Loop**: If relevance score is low, automatically rewrites the search query and re-retrieves before passing to LLM synthesis!

---

## Directory Structure

```
Personal-RAG/
|
+-- .venv/                     # Python Virtual Environment
+-- .streamlit/                # Streamlit UI Theme Configuration
|   +-- config.toml
|
+-- app.py                     # Streamlit Web Application Interface
+-- main.py                    # End-to-end CLI execution script
|
+-- data/                      # Your career info (YAML, Markdown, LaTeX, PDF)
|   +-- profile.yaml           # Bio summary & target roles
|   +-- experiences.yaml       # Work history with STAR bullets & tech tags
|   +-- projects.yaml          # Major projects & achievements
|   +-- skills.yaml            # Skills matrix
|   +-- strengths.yaml         # Behavioral scenarios & growth areas
|
+-- src/                       # Core modular pipeline
|   +-- schema.py              # Pydantic models & DocumentChunk definition
|   +-- loader.py              # Ingests YAML files into typed objects
|   +-- serializer.py          # Serializes structured data into vector chunks
|   +-- embedder.py            # Local SentenceTransformers embedding wrapper
|   +-- store.py               # ChromaDB vector database manager
|   +-- jd_parser.py           # Extracts skills & responsibilities from JDs
|   +-- retriever.py           # Hybrid vector + metadata search engine
|   +-- generator.py           # LLM RAG synthesis engine
|   +-- ollama_provider.py     # Local Ollama LLM provider
|   +-- langgraph_rag.py       # LangGraph agentic RAG workflow
|   +-- latex_exporter.py      # LaTeX resume rendering engine
|   +-- github_fetcher.py      # GitHub profile & repository README fetcher
|   |
|   +-- ingestors/             # Universal Document Ingestion Suite
|       +-- md_ingestor.py     # Markdown README header chunker & tech tagger
|       +-- tex_ingestor.py    # LaTeX document & section parser
|       +-- pdf_ingestor.py    # PDF document page-level parser
|       +-- universal_loader.py# Automated multi-format loader & router
|
+-- templates/
|   +-- resume_template.tex    # Dynamic LaTeX resume template
|
+-- tests/                     # Pipeline tests
+-- README.md
+-- requirements.txt
```

---

## Quick Start Guide

### 1. Virtual Environment Setup
```bash
# Create & activate virtual environment
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Streamlit Web App
```bash
streamlit run app.py
```

### 3. Deploy to Streamlit Community Cloud (Free Hosting)
1. Push repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository and select `app.py` as the main file path!
