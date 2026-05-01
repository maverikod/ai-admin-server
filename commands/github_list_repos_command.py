from ai_admin.core.custom_exceptions import AuthenticationError, CustomError
"""GitHub list repositories command for listing GitHub repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import requests
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.github_security_adapter import GitHubSecurityAdapter

class GitHubListReposCommand(BaseUnifiedCommand):
    """List GitHub repositories for the authenticated user."""

    name = "github_list_repos"

    def __init__(self):
        """Initialize GitHub list repos command."""
        super().__init__()
        self.security_adapter = GitHubSecurityAdapter()

    async def execute(
        self,
        type: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
        username: Optional[str] = None,
        token: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute GitHub list repositories command with unified security.

        Args:
            type: Repository type (all, owner, public, private, member)
            sort: Sort by (created, updated, pushed, full_name)
            direction: Sort direction (asc, desc)
            per_page: Number of repositories per page
            page: Page number
            username: GitHub username
            token: GitHub token
            user_roles: List of user roles for security validation

        Returns:
            Success result with repositories list
        """
        # Use unified security approach
        return await super().execute(
            type=type,
            sort=sort,
            direction=direction,
            per_page=per_page,
            page=page,
            username=username,
            token=token,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for GitHub list repos command."""
        return "github:list_repos"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute GitHub list repositories command logic."""
        return await self._list_repositories(**kwargs)

    async def _list_repositories(
        self,
        type: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
        username: Optional[str] = None,
        token: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """List GitHub repositories."""
        try:
            # Get GitHub token
            if not token:
                from ai_admin.commands.git_utils import get_github_token
                token = get_github_token()

            if not token:
                raise AuthenticationError("GitHub token not found in configuration")

            # Prepare request parameters
            params = {
                "type": type,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page,
            }

            # Make API request
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            if username:
                url = f"https://api.github.com/users/{username}/repos"
            else:
                url = "https://api.github.com/user/repos"

            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                raise CustomError(f"GitHub API error: {response.status_code} - {response.text}")

            repositories = response.json()

            # Extract repository information
            repo_list = []
            for repo in repositories:
                repo_info = {
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "private": repo.get("private"),
                    "html_url": repo.get("html_url"),
                    "clone_url": repo.get("clone_url"),
                    "ssh_url": repo.get("ssh_url"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                    "forks": repo.get("forks_count"),
                    "updated_at": repo.get("updated_at"),
                    "created_at": repo.get("created_at"),
                }
                repo_list.append(repo_info)

            return {
                "message": f"Found {len(repo_list)} repositories",
                        "type": type,
                        "sort": sort,
                        "direction": direction,
                "per_page": per_page,
                "page": page,
                "username": username,
                "repositories": repo_list,
                "count": len(repo_list),
                "total_count": len(repositories),
            }

        except requests.exceptions.RequestException as e:
            raise CustomError(f"GitHub API request failed: {str(e)}")
        except CustomError as e:
            raise CustomError(f"GitHub repositories listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for GitHub list repositories command parameters."""
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "description": "Repository type (all, owner, public, private, member)",
                    "default": "all",
                    "enum": ["all", "owner", "public", "private", "member"],
                },
                "sort": {
                    "type": "string",
                    "description": "Sort by (created, updated, pushed, full_name)",
                    "default": "updated",
                    "enum": ["created", "updated", "pushed", "full_name"],
                },
                "direction": {
                    "type": "string",
                    "description": "Sort direction (asc, desc)",
                    "default": "desc",
                    "enum": ["asc", "desc"],
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of repositories per page",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 100,
                },
                "page": {
                    "type": "integer",
                    "description": "Page number",
                    "default": 1,
                    "minimum": 1,
                },
                "username": {
                    "type": "string",
                    "description": "GitHub username",
                },
                "token": {
                    "type": "string",
                    "description": "GitHub token",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
