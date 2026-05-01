from ai_admin.core.custom_exceptions import CustomError
"""Git utilities for common Git operations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import subprocess
from typing import Dict, Any, Optional

def load_config() -> Dict[str]:
    """Load configuration from config file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
        if os.path.exists(config_path):
            import json
            with open(config_path, "r") as f:
                return json.load(f)
        return {}
    except CustomError:
        return {}

def get_github_token() -> Optional[str]:
    """Get GitHub token from configuration."""
    config = load_config()
    return config.get("github", {}).get("token")

def setup_git_credentials(repo_path: str) -> bool:
    """Setup Git credentials for the repository to use GitHub token.

    Args:
        repo_path: Path to the Git repository

    Returns:
        True if setup was successful, False otherwise
    """
    try:
        github_token = get_github_token()
        if not github_token:
            return False

        # Set up Git credentials
        subprocess.run(
            ["git", "config", "credential.helper", "store"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # Set up remote URL with token
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            remote_url = result.stdout.strip()
            if "github.com" in remote_url and "://" in remote_url:
                # Replace with token-based URL
                if remote_url.startswith("https://"):
                    new_url = remote_url.replace("https://", f"https://{github_token}@")
                elif remote_url.startswith("http://"):
                    new_url = remote_url.replace("http://", f"http://{github_token}@")
                else:
                    new_url = remote_url

                subprocess.run(
                    ["git", "remote", "set-url", "origin", new_url],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                )

        return True

    except CustomError:
        return False

def get_repo_info(repo_path: str) -> Dict[str, Any]:
    """Get repository information.

    Args:
        repo_path: Path to the Git repository

    Returns:
        Dictionary with repository information
    """
    try:
        info = {}

        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["current_branch"] = result.stdout.strip()

        # Get remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["remote_url"] = result.stdout.strip()

        # Get last commit
        result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            info["last_commit"] = result.stdout.strip()

        return info

    except CustomError:
        return {}

def is_git_repo(path: str) -> bool:
    """Check if path is a Git repository.

    Args:
        path: Path to check

    Returns:
        True if path is a Git repository, False otherwise
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
        )
        return result.returncode == 0
    except CustomError:
        return False

def get_git_status(repo_path: str) -> Dict[str, Any]:
    """Get Git repository status.

    Args:
        repo_path: Path to the Git repository

    Returns:
        Dictionary with Git status information
    """
    try:
        status = {}

        # Get status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            status["porcelain"] = result.stdout.strip()

        # Get branch info
        result = subprocess.run(
            ["git", "status", "--branch", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines and lines[0].startswith("##"):
                status["branch_info"] = lines[0]

        return status

    except CustomError:
        return {}
