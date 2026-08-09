# Personal Career RAG and Agentic Assistant

A modular, local-first Retrieval-Augmented Generation (RAG) pipeline designed to ingest personal career documents (Markdown READMEs, LaTeX files, PDFs, and YAML) and tailor them against specific Job Descriptions (JDs).

Includes support for Local LLMs via Ollama, ChromaDB Vector Store, and LangGraph Agentic Workflows with self-correction loops.

---



## Key Features Explained

### 1. Universal Multi-Format Document Ingestion (`src/ingestors/`)
You can drop any of the following files into the `data/` folder:
- **Markdown READMEs (`.md`)**: Automatically splits project READMEs by headers (`#`, `##`) and auto-extracts technology tags.
- **LaTeX Files (`.tex`)**: Parses LaTeX resume templates or past LaTeX documents into section blocks.
- **PDF Documents (`.pdf`)**: Extracts text page-by-page.
- **Structured YAML (`.yaml`)**: Stores structured STAR bullet points (Situation, Action, Result) linked to companies and tech tags.

### 2. Local LLMs via Ollama (`src/ollama_provider.py`)
Run private open-weight models (`llama3.2`, `mistral`, `qwen2.5`, `deepseek-r1`) locally on your machine with 0 cloud cost:
```bash
# Download & launch Ollama locally: https://ollama.com
ollama run llama3.2
```

### 3. LangGraph Agentic RAG and Self-Correction (`src/langgraph_rag.py`)
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
|   +-- test_ingestion.py
|   +-- test_vector_store.py
|   +-- test_latex_export.py
|   +-- test_universal_and_agentic.py
|
+-- main.py                    # End-to-end execution script
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

### 2. Ingest Your Whole Project README / PDF / LaTeX / YAML
Drop any project `README.md`, LaTeX resume (`.tex`), or PDF file into the `data/` directory.

### 3. Run the End-to-End Pipeline
```bash
python main.py
```

### 4. Run LangGraph and Universal Ingestion Tests
```bash
python tests/test_universal_and_agentic.py
```
