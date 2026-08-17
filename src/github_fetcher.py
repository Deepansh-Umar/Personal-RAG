import re
import json
import urllib.request
from typing import List, Dict, Any, Optional
from src.schema import DocumentChunk
from src.ingestors.md_ingestor import MarkdownIngestor


class GitHubProfileIngestor:
    """
    Fetches public GitHub repositories for a given username/profile URL,
    extracts README.md contents from each repository, and converts them into
    searchable DocumentChunks for vector search.
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
        Main entry point: Fetches all repos & READMEs for a profile and converts them into DocumentChunks.
        """
        username = self.extract_username(profile_url_or_username)
        print(f"\n[+] Ingesting GitHub Profile for user: '{username}'...")

        repos = self.fetch_user_repos(username)
        print(f" -> Found {len(repos)} public repositories.")

        all_chunks: List[DocumentChunk] = []

        for repo in repos:
            repo_name = repo.get("name", "")
            description = repo.get("description", "") or "No description provided."
            language = repo.get("language", "") or "N/A"
            stars = repo.get("stargazers_count", 0)

            readme_text = self.fetch_raw_readme(username, repo_name)

            if readme_text and len(readme_text.strip()) > 30:
                chunks = self.md_ingestor.parse_text(readme_text, filename=f"GitHub_{repo_name}_README.md")
                # Enrich metadata with repo details
                for c in chunks:
                    c.metadata["repo_name"] = repo_name
                    c.metadata["repo_url"] = repo.get("html_url", "")
                    c.metadata["primary_language"] = language
                    c.metadata["stars"] = stars
                    c.domain_tags.extend(["github_repo", repo_name.lower()])
                all_chunks.extend(chunks)
            else:
                # Fallback summary chunk from repo metadata
                chunk_id = f"gh_{username.lower()}_{repo_name.lower()}"
                content = (
                    f"GitHub Repository: {repo_name}\n"
                    f"Description: {description}\n"
                    f"Primary Language: {language} | Stars: {stars}\n"
                    f"URL: {repo.get('html_url', '')}"
                )
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_type="project",
                        title=f"GitHub Repo: {repo_name}",
                        content=content,
                        tech_stack=[language] if language != "N/A" else [],
                        domain_tags=["github_repo", repo_name.lower()],
                        metadata={"repo_name": repo_name, "primary_language": language, "stars": stars}
                    )
                )

        print(f" [+] Generated {len(all_chunks)} DocumentChunks from GitHub repositories!")
        return all_chunks
