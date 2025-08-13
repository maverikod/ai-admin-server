"""Git utilities for automatic token configuration."""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


def load_config() -> Dict[str, Any]:
    """Load configuration from config file."""
    try:
        config_path = Path("config/config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
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
        # Get GitHub token
        token = get_github_token()
        if not token:
            return False
        
        # Change to repository directory
        original_cwd = os.getcwd()
        os.chdir(repo_path)
        
        try:
            # Configure credential helper
            subprocess.run(
                ["git", "config", "credential.helper", "store"],
                check=True,
                capture_output=True
            )
            
            # Configure URL with token
            token_url = f"https://{token}@github.com/"
            subprocess.run(
                ["git", "config", "url", f'"{token_url}"', ".insteadOf", "https://github.com/"],
                check=True,
                capture_output=True
            )
            
            # Update remote URLs to use token
            result = subprocess.run(
                ["git", "remote", "-v"],
                check=True,
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.split('\n'):
                if 'origin' in line and 'github.com' in line:
                    # Extract current URL
                    parts = line.split()
                    if len(parts) >= 2:
                        current_url = parts[1]
                        if 'github.com' in current_url and token not in current_url:
                            # Update URL to include token
                            if current_url.startswith('https://github.com/'):
                                new_url = current_url.replace('https://github.com/', token_url)
                                subprocess.run(
                                    ["git", "remote", "set-url", "origin", new_url],
                                    check=True,
                                    capture_output=True
                                )
            
            return True
            
        finally:
            os.chdir(original_cwd)
            
    except Exception:
        return False


def ensure_git_auth(repo_path: str) -> bool:
    """Ensure Git authentication is properly configured.
    
    Args:
        repo_path: Path to the Git repository
        
    Returns:
        True if authentication is configured, False otherwise
    """
    try:
        # Check if token is available
        token = get_github_token()
        if not token:
            return False
        
        # Setup credentials
        return setup_git_credentials(repo_path)
        
    except Exception:
        return False


def get_git_remote_url(repo_path: str, remote: str = "origin") -> Optional[str]:
    """Get Git remote URL.
    
    Args:
        repo_path: Path to the Git repository
        remote: Remote name (default: origin)
        
    Returns:
        Remote URL or None if not found
    """
    try:
        original_cwd = os.getcwd()
        os.chdir(repo_path)
        
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        finally:
            os.chdir(original_cwd)
            
    except Exception:
        return None


def is_github_repo(repo_path: str) -> bool:
    """Check if repository is a GitHub repository.
    
    Args:
        repo_path: Path to the Git repository
        
    Returns:
        True if it's a GitHub repository, False otherwise
    """
    url = get_git_remote_url(repo_path)
    return url and 'github.com' in url if url else False 