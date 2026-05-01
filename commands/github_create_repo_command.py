from ai_admin.core.custom_exceptions import AuthenticationError, CustomError
"""GitHub create repository command for creating GitHub repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import requests
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.github_security_adapter import GitHubSecurityAdapter

class GitHubCreateRepoCommand(BaseUnifiedCommand):
    """Create a new GitHub repository using GitHub API."""

    name = "github_create_repo"

    def __init__(self):
        """Initialize GitHub create repo command."""
        super().__init__()
        self.security_adapter = GitHubSecurityAdapter()

    async def execute(
        self,
        repo_name: str,
        description: Optional[str] = None,
        private: bool = False,
        initialize: bool = False,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
        username: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute GitHub create repository command with unified security.

        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Make repository private
            initialize: Initialize with README
            gitignore_template: Gitignore template
            license_template: License template
            username: GitHub username
            user_roles: List of user roles for security validation

        Returns:
            Success result with repository information
        """
        # Validate inputs
        if not repo_name:
            return ErrorResult(message="Repository name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            repo_name=repo_name,
            description=description,
            private=private,
            initialize=initialize,
            gitignore_template=gitignore_template,
            license_template=license_template,
            username=username,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for GitHub create repo command."""
        return "github:create_repo"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute GitHub create repository command logic."""
        return await self._create_repository(**kwargs)

    async def _create_repository(
        self,
        repo_name: str,
        description: Optional[str] = None,
        private: bool = False,
        initialize: bool = False,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None,
        username: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create GitHub repository."""
        try:
            # Get GitHub token
            from ai_admin.commands.git_utils import get_github_token
            github_token = get_github_token()

            if not github_token:
                raise AuthenticationError("GitHub token not found in configuration")

            # Prepare repository data
            repo_data = {
                "name": repo_name,
                "description": description or "",
                "private": private,
                "auto_init": initialize,
            }

            if gitignore_template:
                repo_data["gitignore_template"] = gitignore_template
            if license_template:
                repo_data["license_template"] = license_template

            # Make API request
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            url = "https://api.github.com/user/repos"
            if username:
                url = f"https://api.github.com/repos/{username}/{repo_name}"

            response = requests.post(url, json=repo_data, headers=headers, timeout=30)

            if response.status_code not in [200, 201]:
                raise CustomError(f"GitHub API error: {response.status_code} - {response.text}")

            repo_info = response.json()

            return {
                "message": f"Successfully created repository '{repo_name}'",
                "repo_name": repo_name,
                "description": description,
                "private": private,
                "initialize": initialize,
                "gitignore_template": gitignore_template,
                "license_template": license_template,
                "username": username,
                "repo_url": repo_info.get("html_url"),
                "clone_url": repo_info.get("clone_url"),
                "ssh_url": repo_info.get("ssh_url"),
                "repo_info": repo_info,
            }

        except requests.exceptions.RequestException as e:
            raise CustomError(f"GitHub API request failed: {str(e)}")
        except CustomError as e:
            raise CustomError(f"GitHub repository creation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for GitHub create repository command parameters."""
        return {
            "type": "object",
            "properties": {
                "repo_name": {
                    "type": "string",
                    "description": "Name of the repository",
                },
                "description": {
                    "type": "string",
                    "description": "Repository description",
                },
                "private": {
                    "type": "boolean",
                    "description": "Make repository private",
                    "default": False,
                },
                "initialize": {
                    "type": "boolean",
                    "description": "Initialize with README",
                    "default": False,
                },
                "gitignore_template": {
                    "type": "string",
                    "description": "Gitignore template",
                },
                "license_template": {
                    "type": "string",
                    "description": "License template",
                },
                "username": {
                    "type": "string",
                    "description": "GitHub username",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["repo_name"],
            "additionalProperties": False,
        }
