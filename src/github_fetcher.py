import re
import json
import urllib.request
from typing import List, Dict, Any, Optional
from src.schema import DocumentChunk
from src.ingestors.md_ingestor import MarkdownIngestor


class GitHubProfileIngestor:
    """
    Fetches public GitHub repositories and Profile README for a given username,
    capturing exact repository URLs (html_url) and live hosted URLs (homepage).
    """

    def __init__(self):
        self.md_ingestor = MarkdownIngestor()

    def extract_username(self, profile_url_or_username: str) -> str:
        """Extracts clean username from full URL or raw string."""
        cleaned = profile_url_or_username.strip().rstrip("/")
        if "github.com/" in cleaned:
            username = cleaned.split("github.com/")[-1].split("/")[0]
        else:
            username = cleaned
        return username

    def fetch_user_repos(self, username: str) -> List[Dict[str, Any]]:
        """Fetches list of public repositories using GitHub API."""
        url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
        headers = {"User-Agent": "Personal-RAG-Assistant"}
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data
        except Exception as e:
            print(f"⚠️ Error fetching repos for GitHub user '{username}': {e}")
        return []

    def fetch_raw_readme(self, username: str, repo_name: str) -> Optional[str]:
        """Tries downloading raw README.md for main or master branch."""
        branches = ["main", "master"]
        headers = {"User-Agent": "Personal-RAG-Assistant"}

        for branch in branches:
            raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{branch}/README.md"
            req = urllib.request.Request(raw_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return response.read().decode("utf-8", errors="ignore")
            except Exception:
                continue
        return None

    def ingest_github_profile(self, profile_url_or_username: str) -> List[DocumentChunk]:
        """
        Main entry point:
        1. FIRST PRIORITY: Fetches main Profile README ({username}/{username}).
        2. SECOND PRIORITY: Fetches all public repository READMEs + exact repo & live URLs.
        """
        username = self.extract_username(profile_url_or_username)
        print(f"\n[+] Ingesting GitHub Profile & Repos for user: '{username}'...")

        all_chunks: List[DocumentChunk] = []

        # 1. PRIORITY 1: Fetch Main GitHub Profile README ({username}/{username})
        profile_readme_text = self.fetch_raw_readme(username, username)
        if profile_readme_text and len(profile_readme_text.strip()) > 30:
            print(" -> [Priority 1] Found Main GitHub Profile README!")
            profile_chunks = self.md_ingestor.parse_text(profile_readme_text, filename=f"GitHub_Profile_README_{username}.md")
            for c in profile_chunks:
                c.source_type = "profile"
                c.domain_tags.extend(["github_profile_readme", "top_skills"])
                c.metadata["priority"] = "high"
                c.metadata["github_url"] = f"https://github.com/{username}"
            all_chunks.extend(profile_chunks)

        # 2. PRIORITY 2: Fetch Public Repositories & Repo READMEs
        repos = self.fetch_user_repos(username)
        print(f" -> [Priority 2] Found {len(repos)} public repositories.")

        for repo in repos:
            repo_name = repo.get("name", "")
            if repo_name.lower() == username.lower():
                continue

            description = repo.get("description", "") or "No description provided."
            language = repo.get("language", "") or "N/A"
            stars = repo.get("stargazers_count", 0)
            repo_url = repo.get("html_url", f"https://github.com/{username}/{repo_name}")
            homepage = repo.get("homepage", "") or ""

            readme_text = self.fetch_raw_readme(username, repo_name)

            if readme_text and len(readme_text.strip()) > 30:
                chunks = self.md_ingestor.parse_text(readme_text, filename=f"GitHub_{repo_name}_README.md")
                for c in chunks:
                    c.metadata["repo_name"] = repo_name
                    c.metadata["repo_url"] = repo_url
                    c.metadata["live_url"] = homepage
                    c.metadata["primary_language"] = language
                    c.metadata["stars"] = stars
                    c.domain_tags.extend(["github_repo", repo_name.lower()])
                all_chunks.extend(chunks)
            else:
                chunk_id = f"gh_{username.lower()}_{repo_name.lower()}"
                content = (
                    f"GitHub Repository: {repo_name}\n"
                    f"Description: {description}\n"
                    f"Primary Language: {language} | Stars: {stars}\n"
                    f"Repository URL: {repo_url}\n"
                    + (f"Live Hosted URL: {homepage}\n" if homepage else "")
                )
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_type="project",
                        title=f"GitHub Repo: {repo_name}",
                        content=content,
                        tech_stack=[language] if language != "N/A" else [],
                        domain_tags=["github_repo", repo_name.lower()],
                        metadata={"repo_name": repo_name, "repo_url": repo_url, "live_url": homepage, "primary_language": language, "stars": stars}
                    )
                )

        print(f" [+] Generated {len(all_chunks)} total DocumentChunks from GitHub!")
        return all_chunks
