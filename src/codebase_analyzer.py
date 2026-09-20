import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

PYTHON_IMPORT_PATTERN = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', re.MULTILINE)
JS_IMPORT_PATTERN = re.compile(r'(?:import\s+.*?from\s+[\'"]([^\'"]+)[\'"]|require\([\'"]([^\'"]+)[\'"]\))')

# Standard library filters to exclude common built-ins
PY_STDLIB = {
    "os", "sys", "re", "json", "math", "time", "datetime", "random", "typing", "pathlib", 
    "collections", "functools", "itertools", "subprocess", "copy", "shutil", "io", "base64", 
    "urllib", "hashlib", "argparse", "logging", "asyncio", "threading", "multiprocessing", 
    "glob", "csv", "pickle", "inspect", "ast", "tempfile"
}

KNOWN_TECH_MAP = {
    # AI / ML / DL
    "torch": "PyTorch",
    "torchvision": "PyTorch / Computer Vision",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "sklearn": "Scikit-Learn",
    "lightgbm": "LightGBM",
    "xgboost": "XGBoost",
    "scipy": "SciPy",
    "cv2": "OpenCV",
    "PIL": "Pillow / Image Processing",
    
    # Data Science & NLP
    "pandas": "Pandas",
    "numpy": "NumPy",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "nltk": "NLTK",
    "spacy": "spaCy",
    "transformers": "HuggingFace Transformers",
    "chromadb": "ChromaDB",
    "sentence_transformers": "SentenceTransformers",
    "langchain": "LangChain",
    "langgraph": "LangGraph",
    "google.generativeai": "Google Gemini API",
    "genai": "Google Gemini API",
    "anthropic": "Claude API",
    "ollama": "Ollama",

    # Web & Backend
    "flask": "Flask",
    "fastapi": "FastAPI",
    "django": "Django",
    "sqlalchemy": "SQLAlchemy",
    "psycopg2": "PostgreSQL",
    "redis": "Redis",
    "celery": "Celery",
    "jwt": "JWT",
    "requests": "REST APIs",
    "bs4": "BeautifulSoup / Web Scraping",
    "selenium": "Selenium Automation",
    "streamlit": "Streamlit",
    
    # JS / Frontend
    "react": "React",
    "vue": "Vue.js",
    "express": "Express.js",
    "axios": "Axios",
    "bootstrap": "Bootstrap"
}

def analyze_repository(repo_path: Path) -> Dict[str, Any]:
    file_counts = {}
    total_loc = 0
    detected_imports: Set[str] = set()
    dependencies_found: Set[str] = set()
    key_files = []
    has_readme = False
    readme_content = ""

    for root, dirs, files in os.walk(repo_path):
        # Ignore hidden / build dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', 'env', 'dist', 'build')]

        for f in files:
            file_path = Path(root) / f
            ext = file_path.suffix.lower()
            file_counts[ext] = file_counts.get(ext, 0) + 1

            rel_path = file_path.relative_to(repo_path)
            key_files.append(str(rel_path))

            # Check README
            if f.lower().startswith('readme'):
                has_readme = True
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as rf:
                        readme_content = rf.read(4000)
                except Exception:
                    pass

            # Check package specifications
            if f == 'requirements.txt' or f == 'Pipfile':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as pf:
                        for line in pf:
                            line = line.strip().split('#')[0].split('==')[0].split('>=')[0].strip()
                            if line:
                                dependencies_found.add(line.lower())
                except Exception:
                    pass

            if f == 'package.json':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as pjf:
                        pj = json.load(pjf)
                        deps = {**pj.get('dependencies', {}), **pj.get('devDependencies', {})}
                        for dep in deps:
                            dependencies_found.add(dep.lower())
                except Exception:
                    pass

            # Scan source files for imports & LOC
            if ext in ('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.html', '.css', '.ipynb'):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as sf:
                        content = sf.read()
                        total_loc += len(content.splitlines())

                        if ext == '.py':
                            matches = PYTHON_IMPORT_PATTERN.findall(content)
                            for m in matches:
                                root_pkg = m.split('.')[0]
                                if root_pkg not in PY_STDLIB:
                                    detected_imports.add(root_pkg.lower())
                        elif ext in ('.js', '.jsx', '.ts', '.tsx'):
                            matches = JS_IMPORT_PATTERN.findall(content)
                            for m_tuple in matches:
                                dep = m_tuple[0] or m_tuple[1]
                                if dep and not dep.startswith('.'):
                                    pkg = dep.split('/')[0]
                                    detected_imports.add(pkg.lower())
                except Exception:
                    pass

    # Normalize detected tech stack
    tech_stack = set()
    all_found = detected_imports.union(dependencies_found)
    for pkg in all_found:
        if pkg in KNOWN_TECH_MAP:
            tech_stack.add(KNOWN_TECH_MAP[pkg])

    # Language distribution
    lang_map = {
        '.py': 'Python',
        '.ipynb': 'Jupyter Notebook',
        '.js': 'JavaScript',
        '.jsx': 'React / JS',
        '.ts': 'TypeScript',
        '.html': 'HTML',
        '.css': 'CSS',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.sql': 'SQL'
    }

    primary_languages = set()
    for ext, count in file_counts.items():
        if ext in lang_map:
            primary_languages.add(lang_map[ext])
            tech_stack.add(lang_map[ext])

    # Categorize domain
    tech_lower = " ".join([t.lower() for t in tech_stack]) + " " + readme_content.lower() + " " + repo_path.name.lower()
    
    domain_category = "General Software Engineering"
    if any(k in tech_lower for k in ["pytorch", "torch", "tensorflow", "keras", "deep learning", "neural network", "perception", "computer vision"]):
        domain_category = "AI / Machine Learning & Deep Learning"
    elif any(k in tech_lower for k in ["nlp", "sentiment", "rag", "chromadb", "langchain", "gemini", "claude", "ollama", "llm", "transformers", "text"]):
        domain_category = "NLP & Large Language Models (LLMs)"
    elif any(k in tech_lower for k in ["flask", "fastapi", "django", "react", "vue", "express", "postgresql", "redis", "celery", "web", "parking", "url"]):
        domain_category = "Web Engineering & Full-Stack Systems"
    elif any(k in tech_lower for k in ["pandas", "numpy", "eda", "visualization", "data analysis", "housing", "diabetes", "medical"]):
        domain_category = "Data Science & Analytics"
    elif any(k in tech_lower for k in ["leetcode", "dsa", "algorithm", "data structure", "c++", "cpp", "java", "python Gold badge"]):
        domain_category = "Data Structures & Algorithms / Problem Solving"
    elif any(k in tech_lower for k in ["organizer", "file", "automation", "utility", "script"]):
        domain_category = "System Utilities & Automation Tools"

    return {
        "repo_name": repo_path.name,
        "total_loc": total_loc,
        "file_extension_counts": file_counts,
        "primary_languages": sorted(list(primary_languages)),
        "detected_tech_stack": sorted(list(tech_stack)),
        "raw_imports": sorted(list(detected_imports)),
        "raw_dependencies": sorted(list(dependencies_found)),
        "domain_category": domain_category,
        "has_readme": has_readme,
        "readme_excerpt": readme_content[:1000].strip(),
        "file_sample": key_files[:15]
    }

def run_deep_codebase_analysis():
    base_dir = Path(__file__).parent.parent
    cloned_dir = base_dir / "cloned_repos"
    output_cache_path = base_dir / "data" / "codebase_analysis_cache.json"

    if not cloned_dir.exists():
        safe_print(f"[ERROR] {cloned_dir} does not exist. Run src/repo_cloner.py first.")
        return

    repo_dirs = [d for d in cloned_dir.iterdir() if d.is_dir()]
    safe_print(f"[Phase 2] Analyzing {len(repo_dirs)} cloned repositories...")

    analysis_results = {}
    for idx, rdir in enumerate(repo_dirs, 1):
        safe_print(f"[{idx}/{len(repo_dirs)}] Analyzing codebase for {rdir.name}...")
        try:
            repo_data = analyze_repository(rdir)
            analysis_results[rdir.name] = repo_data
            safe_print(f"    -> Category: {repo_data['domain_category']} | Tech Stack: {', '.join(repo_data['detected_tech_stack'][:4])}")
        except Exception as e:
            safe_print(f"    -> Error analyzing {rdir.name}: {e}")

        # Checkpoint save intermediate results
        with open(output_cache_path, "w", encoding="utf-8") as f:
            json.dump(analysis_results, f, indent=2)

    safe_print(f"\n✅ Phase 2 Complete! Analysis of {len(analysis_results)} repositories saved to {output_cache_path}")

if __name__ == "__main__":
    run_deep_codebase_analysis()
