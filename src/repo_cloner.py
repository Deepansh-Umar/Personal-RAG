import os
import sys
import yaml
import json
import subprocess
from pathlib import Path

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'ignore').decode('ascii'))

def clone_all_repos():
    base_dir = Path(__file__).parent.parent
    data_file = base_dir / "data" / "github_deep_extract.yaml"
    target_dir = base_dir / "cloned_repos"
    target_dir.mkdir(parents=True, exist_ok=True)
    status_log_path = base_dir / "data" / "clone_status.json"

    if not data_file.exists():
        safe_print(f"[ERROR] {data_file} not found.")
        sys.exit(1)

    with open(data_file, "r", encoding="utf-8") as f:
        repos = yaml.safe_load(f) or []

    safe_print(f"[Phase 1] Starting cloning of {len(repos)} repositories into {target_dir}...")
    
    clone_results = {}
    if status_log_path.exists():
        with open(status_log_path, "r", encoding="utf-8") as f:
            try:
                clone_results = json.load(f)
            except Exception:
                pass

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for idx, repo_info in enumerate(repos, 1):
        repo_name = repo_info.get("repo_name") or repo_info.get("id", f"repo_{idx}")
        github_url = repo_info.get("github_url")

        if not github_url:
            safe_print(f"[{idx}/{len(repos)}] Skipping {repo_name} (no github_url provided)")
            continue

        local_repo_path = target_dir / repo_name

        if local_repo_path.exists() and (local_repo_path / ".git").exists():
            safe_print(f"[{idx}/{len(repos)}] Already cloned: {repo_name}")
            clone_results[repo_name] = {
                "status": "success",
                "path": str(local_repo_path),
                "url": github_url
            }
            skipped_count += 1
            continue

        safe_print(f"[{idx}/{len(repos)}] Cloning {repo_name} from {github_url}...")
        cmd = ["git", "clone", "--depth", "1", github_url, str(local_repo_path)]
        
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                safe_print(f"    -> Cloned successfully.")
                clone_results[repo_name] = {
                    "status": "success",
                    "path": str(local_repo_path),
                    "url": github_url
                }
                success_count += 1
            else:
                safe_print(f"    -> Failed: {res.stderr.strip()}")
                clone_results[repo_name] = {
                    "status": "failed",
                    "error": res.stderr.strip(),
                    "url": github_url
                }
                failed_count += 1
        except Exception as e:
            safe_print(f"    -> Error cloning {repo_name}: {e}")
            clone_results[repo_name] = {
                "status": "error",
                "error": str(e),
                "url": github_url
            }
            failed_count += 1

        # Checkpoint save status log after every repo
        with open(status_log_path, "w", encoding="utf-8") as f:
            json.dump(clone_results, f, indent=2)

    safe_print("\n================ CLONING SUMMARY ================")
    safe_print(f"Total Repositories Processed: {len(repos)}")
    safe_print(f"Newly Cloned: {success_count}")
    safe_print(f"Already Existed: {skipped_count}")
    safe_print(f"Failed: {failed_count}")
    safe_print(f"Status saved to: {status_log_path}")

if __name__ == "__main__":
    clone_all_repos()
