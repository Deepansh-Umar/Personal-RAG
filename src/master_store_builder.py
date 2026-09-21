import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

# Repositories to strictly EXCLUDE from Original Software Projects (Forks, Profile READMEs, Raw Markdown Notes, Placeholders)
EXCLUDED_REPOS = {
    "leetcode",          # LeetHub auto-synced competitive coding solutions
    "resources",         # Raw Markdown learning roadmaps / notes
    "deepansh-umar",     # GitHub profile README repo
    "gcc-bose-cgit"      # Static HTML placeholder
}

# Accurate Domain Classification Map based on deep codebase inspection
EXACT_DOMAIN_MAP = {
    # 1. NLP & Large Language Models (LLMs)
    "personal-rag": "NLP & Large Language Models (LLMs)",

    # 2. AI & Machine Learning (ML/DL) - Model Building, Algorithms, Pipelines
    "text_sentiment_classification": "AI & Machine Learning (ML/DL)",
    "phrase-sentiment-analysis": "AI & Machine Learning (ML/DL)",
    "mcq-solver": "AI & Machine Learning (ML/DL)",
    "heavy-machine-price-prediction": "AI & Machine Learning (ML/DL)",
    "california_housing_price_prediction": "AI & Machine Learning (ML/DL)",
    "diabetes-prediction": "AI & Machine Learning (ML/DL)",

    # 3. Data Science & Analytics (DS/DA) - EDA, Statistics, Data Wrangling, Visualization
    "mlp": "Data Science & Analytics (DS/DA)",
    "fcc-dawp-medical_data_visualizer": "Data Science & Analytics (DS/DA)",
    "fcc-dawp-time_series_vizualizer": "Data Science & Analytics (DS/DA)",
    "fcc-dawp-sea_level_predictor": "Data Science & Analytics (DS/DA)",
    "fcc-dawp-demo_data_analyzer": "Data Science & Analytics (DS/DA)",
    "fcc-dawp-mean-std-dev": "Data Science & Analytics (DS/DA)",

    # 4. Web Engineering & Full-Stack Systems
    "parkease-v2": "Web Engineering & Full-Stack Systems",
    "parkease": "Web Engineering & Full-Stack Systems",
    "zeroplast": "Web Engineering & Full-Stack Systems",
    "sih-autohmpi": "Web Engineering & Full-Stack Systems",
    "url-shortner": "Web Engineering & Full-Stack Systems",
    "url-shortener": "Web Engineering & Full-Stack Systems",
    "tds": "Web Engineering & Full-Stack Systems",
    "tesseract_iitm_club": "Web Engineering & Full-Stack Systems",
    "dsa-squad": "Web Engineering & Full-Stack Systems",
    "academic-utility-app": "Web Engineering & Full-Stack Systems",

    # 5. System Utilities & Software Tools
    "file-organizer": "System Utilities & Software Tools",
    "hospital-management": "System Utilities & Software Tools",
    "student-management": "System Utilities & Software Tools",
    "nirmaan-os": "System Utilities & Software Tools",
    "fcc-scwp-polygon-area": "System Utilities & Software Tools",
    "fcc-scwp-probability-calc": "System Utilities & Software Tools"
}

def build_master_project_store():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"

    analysis_cache_path = data_dir / "codebase_analysis_cache.json"
    gh_extract_path = data_dir / "github_deep_extract.yaml"
    career_evidence_path = data_dir / "career_evidence.yaml"

    master_store_path = data_dir / "master_project_store.yaml"
    tech_matrix_path = data_dir / "candidate_tech_matrix.yaml"
    category_index_path = data_dir / "projects_by_category.json"

    analysis_cache = {}
    if analysis_cache_path.exists():
        with open(analysis_cache_path, "r", encoding="utf-8") as f:
            analysis_cache = json.load(f)

    gh_extract = []
    if gh_extract_path.exists():
        with open(gh_extract_path, "r", encoding="utf-8") as f:
            gh_extract = yaml.safe_load(f) or []

    career_evidence = {}
    if career_evidence_path.exists():
        with open(career_evidence_path, "r", encoding="utf-8") as f:
            career_evidence = yaml.safe_load(f) or {}

    master_projects = []
    category_map: Dict[str, List[Dict[str, Any]]] = {
        "AI & Machine Learning (ML/DL)": [],
        "Data Science & Analytics (DS/DA)": [],
        "NLP & Large Language Models (LLMs)": [],
        "Web Engineering & Full-Stack Systems": [],
        "System Utilities & Software Tools": []
    }

    all_languages: Set[str] = set()
    all_aiml: Set[str] = set()
    all_nlp_rag: Set[str] = set()
    all_backend: Set[str] = set()
    all_frontend: Set[str] = set()
    all_databases: Set[str] = set()
    all_tools: Set[str] = set()

    ce_projects = career_evidence.get("projects", [])
    ce_map = {p.get("github_url", "").lower().rstrip('/'): p for p in ce_projects}
    gh_map = {g.get("repo_name", "").lower(): g for g in gh_extract}

    all_repo_names = sorted(list(set(list(analysis_cache.keys()) + list(gh_map.keys()))))

    safe_print(f"[Phase 3] Building Master Knowledge Store for original candidate projects...")

    for rname in all_repo_names:
        rname_lower = rname.lower()

        # Filter out external forks, profile READMEs, and non-project resources
        if rname_lower in EXCLUDED_REPOS:
            safe_print(f" [-] Excluded non-original/fork repo: {rname}")
            continue

        ac = analysis_cache.get(rname, {})
        gh = gh_map.get(rname_lower, {})
        repo_url = gh.get("github_url", f"https://github.com/Deepansh-Umar/{rname}")
        ce_match = ce_map.get(repo_url.lower().rstrip('/'), {})

        # Determine Title
        if ce_match.get("title"):
            title = ce_match["title"]
        elif gh.get("title") and gh["title"] != "Title" and gh["title"] != rname:
            title = gh["title"]
        else:
            title = rname.replace("-", " ").replace("_", " ").title()

        # Combine tech stack
        tech_set = set(ac.get("detected_tech_stack", []))
        if gh.get("primary_language") and gh["primary_language"] != "N/A":
            tech_set.add(gh["primary_language"])
        if ce_match.get("tech_stack"):
            tech_set.update(ce_match["tech_stack"])

        tech_list = sorted(list(tech_set))

        # Assign exact domain based on deep codebase audit
        norm_cat = EXACT_DOMAIN_MAP.get(rname_lower, "System Utilities & Software Tools")

        # Complexity rating
        loc = ac.get("total_loc", 0)
        if loc > 1500 or len(tech_list) >= 5 or ce_match:
            complexity = "High Impact Production / Research Project"
        elif loc > 300 or len(tech_list) >= 3:
            complexity = "Core Application Project"
        else:
            complexity = "Targeted Utility / Academic Project"

        # Resume Bullets Generation
        bullets = []
        if ce_match.get("bullets"):
            for b in ce_match["bullets"]:
                b_text = b.get("text") if isinstance(b, dict) else str(b)
                bullets.append(b_text)
        else:
            desc = gh.get("description", "")
            readme_excerpt = ac.get("readme_excerpt", "")
            if desc and desc != "No description provided.":
                bullets.append(desc)
            elif readme_excerpt and len(readme_excerpt) > 30:
                clean_r = readme_excerpt.replace('#', '').strip()
                bullets.append(clean_r[:220])
            else:
                bullets.append(f"Engineered custom application utilizing {', '.join(tech_list[:3]) if tech_list else 'modern programming principles'}.")

        proj_entry = {
            "id": f"proj_{rname_lower.replace('-', '_')}",
            "title": title,
            "repo_name": rname,
            "github_url": repo_url,
            "live_url": ce_match.get("live_url", gh.get("live_url", "")),
            "domain_category": norm_cat,
            "complexity_rating": complexity,
            "primary_language": gh.get("primary_language", "Python"),
            "loc_estimate": loc,
            "tech_stack": tech_list,
            "purpose_summary": gh.get("description", "") or ac.get("readme_excerpt", "")[:300],
            "resume_bullets": bullets
        }

        master_projects.append(proj_entry)
        if norm_cat in category_map:
            category_map[norm_cat].append(proj_entry)

        # Aggregate verified skills taxonomy
        for t in tech_list:
            if t in ["Python", "Java", "C", "C++", "JavaScript", "TypeScript", "SQL", "HTML", "CSS", "Bash"]:
                all_languages.add(t)
            elif t in ["PyTorch", "TensorFlow", "Keras", "Scikit-Learn", "LightGBM", "XGBoost", "OpenCV", "Pillow", "SciPy"]:
                all_aiml.add(t)
            elif t in ["RAG", "ChromaDB", "SentenceTransformers", "Ollama", "LangChain", "LangGraph", "Google Gemini API", "Claude API"]:
                all_nlp_rag.add(t)
            elif t in ["Flask", "FastAPI", "Express.js", "Celery", "Redis", "SQLAlchemy", "REST APIs", "BeautifulSoup / Web Scraping", "Selenium Automation"]:
                all_backend.add(t)
            elif t in ["React", "Vue.js", "Bootstrap", "Axios"]:
                all_frontend.add(t)
            elif t in ["PostgreSQL", "MySQL", "SQLite", "Redis", "ChromaDB"]:
                all_databases.add(t)
            else:
                all_tools.add(t)

    # Save master_project_store.yaml
    with open(master_store_path, "w", encoding="utf-8") as f:
        yaml.dump(master_projects, f, default_flow_style=False, sort_keys=False)
    safe_print(f" [+] Master Project Knowledge Store written: {master_store_path} ({len(master_projects)} original projects)")

    # Save candidate_tech_matrix.yaml
    candidate_tech_matrix = {
        "candidate": "Deepansh Umar",
        "total_original_projects_analyzed": len(master_projects),
        "excluded_non_original_repos": list(EXCLUDED_REPOS),
        "programming_languages": sorted(list(all_languages | {"Python", "Java", "SQL", "JavaScript", "HTML/CSS", "React", "Bash", "C/C++"})),
        "ai_ml_deep_learning": sorted(list(all_aiml | {"PyTorch", "Scikit-Learn", "LightGBM", "XGBoost", "OpenCV"})),
        "nlp_rag_llms": sorted(list(all_nlp_rag | {"Claude API", "Gemini API", "RAG", "ChromaDB", "SentenceTransformers", "Ollama", "LangGraph"})),
        "backend_frameworks": sorted(list(all_backend | {"Flask", "FastAPI", "REST APIs", "PostgreSQL", "Redis", "Celery", "Chrome Extensions"})),
        "frontend_frameworks": sorted(list(all_frontend | {"React", "Vue.js", "HTML5", "CSS3", "JavaScript (ES6+)"})),
        "databases_storage": sorted(list(all_databases | {"PostgreSQL", "MySQL", "SQLite", "Redis", "ChromaDB"})),
        "tools_infrastructure": sorted(list(all_tools | {"Git", "GitHub", "Docker", "LinkedIn Recruiter", "Ceipal", "Postman", "Render", "Vercel", "Jupyter Notebooks"}))
    }

    with open(tech_matrix_path, "w", encoding="utf-8") as f:
        yaml.dump(candidate_tech_matrix, f, default_flow_style=False, sort_keys=False)
    safe_print(f" [+] Candidate Tech Matrix written: {tech_matrix_path}")

    # Save projects_by_category.json
    with open(category_index_path, "w", encoding="utf-8") as f:
        json.dump(category_map, f, indent=2)
    safe_print(f" [+] Projects by Category Index written: {category_index_path}")

    safe_print("\n================ AUDITED MASTER STORE SUMMARY ================")
    for cat_name, proj_list in category_map.items():
        safe_print(f" - {cat_name}: {len(proj_list)} projects")

if __name__ == "__main__":
    build_master_project_store()
