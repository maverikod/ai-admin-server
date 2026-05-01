"""
Base Git Command with Authentication Support

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This module provides a base class for Git commands with built-in
authentication support using SSH keys and tokens.
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from base_unified_command import BaseUnifiedCommand
from ai_admin.auth.git_auth_manager import GitAuthManager, GitAuthConfig

logger = logging.getLogger(__name__)


class BaseGitCommand(BaseUnifiedCommand):
    """
    Base class for Git commands with authentication support.
    
    Features:
    - Automatic SSH key discovery and usage
    - Token-based authentication for HTTPS repositories
    - Passphrase-protected key handling
    - Environment configuration for Git operations
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize base Git command with authentication manager."""
        super().__init__(*args, **kwargs)
        self.auth_manager = GitAuthManager()
    
    def _get_git_env(self, repository_url: Optional[str] = None) -> Dict[str, str]:
        """
        Get environment variables for Git operations with authentication.
        
        Args:
            repository_url: Repository URL for authentication context
            
        Returns:
            Environment variables for Git
        """
        env = os.environ.copy()
        
        if repository_url:
            # Configure authentication based on repository URL
            env.update(self.auth_manager.configure_git_credentials(repository_url))
        else:
            # Use default authentication setup
            ssh_key = self.auth_manager.get_best_ssh_key()
            if ssh_key:
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key.path} -o IdentitiesOnly=yes'
        
        return env
    
    def _run_git_command(self, 
                        command: List[str], 
                        repository_url: Optional[str] = None,
                        cwd: Optional[str] = None,
                        timeout: int = 30) -> subprocess.CompletedProcess:
        """
        Run Git command with proper authentication.
        
        Args:
            command: Git command as list of strings
            repository_url: Repository URL for authentication
            cwd: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            Completed process result
        """
        env = self._get_git_env(repository_url)
        
        # Add force flags for operations that might require confirmation
        if any(cmd in command for cmd in ['push', 'pull', 'merge', 'rebase', 'reset']):
            if '--force' not in command and '-f' not in command:
                # Add appropriate force flag based on command
                if 'push' in command:
                    command.insert(-1, '--force-with-lease')
                elif 'reset' in command:
                    command.insert(-1, '--hard')
        
        # Add yes flags for operations that might prompt
        if any(cmd in command for cmd in ['clean', 'reset', 'checkout']):
            if '--yes' not in command and '-y' not in command:
                command.insert(-1, '--yes')
        
        logger.info(f"Running Git command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Git command failed: {result.stderr}")
            else:
                logger.debug(f"Git command succeeded: {result.stdout}")
                
            return result
            
        except subprocess.TimeoutExpired as e:
            logger.error(f"Git command timed out after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"Error running Git command: {e}")
            raise
    
    def _get_repository_url(self, **kwargs) -> Optional[str]:
        """
        Extract repository URL from command parameters.
        
        Args:
            **kwargs: Command parameters
            
        Returns:
            Repository URL if found
        """
        # Common parameter names for repository URL
        url_params = ['repository_url', 'url', 'remote_url', 'repo_url']
        
        for param in url_params:
            if param in kwargs and kwargs[param]:
                return kwargs[param]
        
        return None
    
    def _setup_authentication(self, repository_url: str) -> bool:
        """
        Set up authentication for the repository.
        
        Args:
            repository_url: Repository URL
            
        Returns:
            True if authentication setup was successful
        """
        try:
            if repository_url.startswith('https://'):
                # HTTPS authentication - check for tokens
                if 'github.com' in repository_url:
                    token = self.auth_manager.get_github_token()
                    if not token:
                        logger.warning("GitHub token not configured")
                        return False
                elif 'gitlab.com' in repository_url:
                    token = self.auth_manager.get_gitlab_token()
                    if not token:
                        logger.warning("GitLab token not configured")
                        return False
                        
            elif repository_url.startswith('git@'):
                # SSH authentication - check for SSH keys
                ssh_keys = self.auth_manager.discover_ssh_keys()
                if not ssh_keys:
                    logger.warning("No SSH keys found")
                    return False
                
                # Try to set up SSH agent
                best_key = self.auth_manager.get_best_ssh_key()
                if best_key and best_key.has_passphrase:
                    logger.warning(f"SSH key {best_key.path} requires passphrase")
                    # In production, you might want to prompt for passphrase
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up authentication: {e}")
            return False
    
    def _validate_git_repository(self, path: str) -> bool:
        """
        Validate that the given path is a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if valid Git repository
        """
        git_dir = Path(path) / '.git'
        return git_dir.exists() and git_dir.is_dir()
    
    def _get_git_root(self, path: str) -> Optional[str]:
        """
        Get the root directory of the Git repository.
        
        Args:
            path: Path within the repository
            
        Returns:
            Git root directory or None
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception as e:
            logger.error(f"Error getting Git root: {e}")
        
        return None
    
    def _is_git_available(self) -> bool:
        """
        Check if Git is available in the system.
        
        Returns:
            True if Git is available
        """
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_git_config(self, key: str, cwd: Optional[str] = None) -> Optional[str]:
        """
        Get Git configuration value.
        
        Args:
            key: Configuration key
            cwd: Working directory
            
        Returns:
            Configuration value or None
        """
        try:
            result = subprocess.run(
                ['git', 'config', '--get', key],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
                
        except Exception as e:
            logger.error(f"Error getting Git config {key}: {e}")
        
        return None
    
    def _set_git_config(self, key: str, value: str, cwd: Optional[str] = None) -> bool:
        """
        Set Git configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            cwd: Working directory
            
        Returns:
            True if successful
        """
        try:
            result = subprocess.run(
                ['git', 'config', key, value],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error setting Git config {key}: {e}")
            return False
