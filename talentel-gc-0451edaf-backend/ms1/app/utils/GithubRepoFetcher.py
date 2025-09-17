import os
import stat
import time

import requests
import shutil
import tempfile
from git import Repo
from typing import Optional, Dict

def get_project_temp_dir():
    project_root = os.getcwd()
    temp_dir = os.path.join(project_root, "temp_repos")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def on_rm_error(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as e:
        print(f"[ERROR] Could not forcibly remove {path}: {e}")

def safe_cleanup(target_dir):
    if os.path.exists(target_dir):
        print(f"[DEBUG] Attempting to clean up: {target_dir}")
        try:
            shutil.rmtree(target_dir, onerror=on_rm_error)
            print(f"[INFO] Successfully cleaned up: {target_dir}")
        except Exception as cleanup_err:
            print(f"[WARN] Could not clean up target dir: {cleanup_err}")
            print(f"[DEBUG] Directory contents after failed cleanup: {os.listdir(target_dir)}")
            time.sleep(1)
            # Optionally, try again
            try:
                shutil.rmtree(target_dir, onerror=on_rm_error)
            except Exception as e:
                print(f"[ERROR] Second cleanup attempt failed: {e}")


class GitHubRepoFetcher:
    def __init__(self, github_token: str, api_base_url: Optional[str] = None, owner: Optional[str] = None):
        self.github_token = github_token
        self.api_base_url = api_base_url or "https://api.github.com/"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_latest_commit_before(self, repo_full_name: str, branch: str, timestamp: str) -> Dict[str, str]:
        url = f"{self.api_base_url}/repos/{repo_full_name}/commits"
        params = {
            "sha": branch,
            "until": timestamp,
            "per_page": 1
        }
        try:
            print(f"[DEBUG] Fetching latest commit before {timestamp} on branch '{branch}' for repo '{repo_full_name}'")
            response = requests.get(url, headers=self.headers, params=params)
            print("[DEBUG] GitHub API response status:", response.status_code)
            response.raise_for_status()
            commits = response.json()
            if not commits:
                raise ValueError(f"No commits found before {timestamp} on branch {branch}")
            commit_info = commits[0]
            print(f"[DEBUG] Found commit: {commit_info['sha']} at {commit_info['commit']['committer']['date']}")
            return {
                "sha": commit_info["sha"],
                "date": commit_info["commit"]["committer"]["date"],
                "message": commit_info["commit"]["message"]
            }
        except Exception as e:
            print(f"[ERROR] Failed to fetch commit: {str(e)}")
            raise

    def get_safe_target_dir(self, repo_full_name: str, assign_id: str) -> str:
        temp_dir = get_project_temp_dir()
        safe_name = repo_full_name.replace('/', '_')
        return os.path.join(temp_dir, f"{safe_name}_{assign_id}")

    def clone_repo_at_commit(self, repo_url: str, commit_sha: str, target_dir: str) -> str:
        try:
            # Clean up target directory if it exists
            safe_cleanup(target_dir)
            print(f"[DEBUG] Cloning repo '{repo_url}' into '{target_dir}'")
            # For private repos, embed token in URL for authentication (avoid printing token)
            safe_repo_url = repo_url
            if self.github_token and "github.com" in repo_url:
                safe_repo_url = repo_url.replace("https://", f"https://{self.github_token}@")
            repo = Repo.clone_from(safe_repo_url, target_dir)
            repo.git.checkout(commit_sha)
            print(f"[DEBUG] Checked out commit {commit_sha}")
            return target_dir
        except Exception as e:
            print(f"[ERROR] Failed to clone repo: {str(e)}")
            raise

    def fetch_repo_at_commit(self, repo_url: str, repo_full_name: str, branch: str, timestamp: str, assign_id: str) -> Dict[str, str]:
        """
        Orchestrates the fetch: gets latest commit before timestamp, clones repo at that commit.
        Returns info dict with local path and commit info.
        """
        try:
            commit_info = self.get_latest_commit_before(repo_full_name, branch, timestamp)
            target_dir = self.get_safe_target_dir(repo_full_name, assign_id)
            self.clone_repo_at_commit(repo_url, commit_info["sha"], target_dir)
            return {
                "success": True,
                "local_path": target_dir,
                "commit_sha": commit_info["sha"],
                "commit_date": commit_info["date"],
                "commit_message": commit_info["message"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
