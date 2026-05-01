from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git clone command for cloning repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitCloneCommand(BaseUnifiedCommand):
    """Clone Git repositories from various sources.

    This command supports cloning from:
    - GitHub (HTTPS/SSH)
    - GitLab
    - Bitbucket
    - Local repositories
    - Custom Git servers
    """

    name = "git_clone"

    def __init__(self):
        """Initialize Git clone command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        repository_url: str,
        target_directory: Optional[str] = None,
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        recursive: bool = False,
        quiet: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git clone command with unified security.

        Args:
            repository_url: URL of the repository to clone
            target_directory: Target directory for clone
            branch: Branch to clone
            depth: Shallow clone depth
            recursive: Recursive clone
            quiet: Quiet mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with clone information
        """
        # Validate inputs
        if not repository_url:
            return ErrorResult(message="Repository URL is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            repository_url=repository_url,
            target_directory=target_directory,
            branch=branch,
            depth=depth,
            recursive=recursive,
            quiet=quiet,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git clone command."""
        return "git:clone"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git clone command logic."""
        return await self._clone_repository(**kwargs)

    async def _clone_repository(
        self,
        repository_url: str,
        target_directory: Optional[str] = None,
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        recursive: bool = False,
        quiet: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Clone Git repository."""
        try:
            # Build Git command
            cmd = ["git", "clone"]

            # Add options
            if branch:
                cmd.extend(["--branch", branch])
            if depth:
                cmd.extend(["--depth", str(depth)])
            if recursive:
                cmd.append("--recursive")
            if quiet:
                cmd.append("--quiet")

            # Add repository URL
            cmd.append(repository_url)

            # Add target directory if specified
            if target_directory:
                cmd.append(target_directory)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                raise CustomError(f"Git clone failed: {result.stderr}")

            return {
                "message": f"Successfully cloned repository '{repository_url}'",
                "repository_url": repository_url,
                "target_directory": target_directory,
                "branch": branch,
                "depth": depth,
                "recursive": recursive,
                "quiet": quiet,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git clone command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git clone failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git clone command parameters."""
        return {
            "type": "object",
            "properties": {
                "repository_url": {
                    "type": "string",
                    "description": "URL of the repository to clone",
                },
                "target_directory": {
                    "type": "string",
                    "description": "Target directory for clone",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch to clone",
                },
                "depth": {
                    "type": "integer",
                    "description": "Shallow clone depth",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Recursive clone",
                    "default": False,
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["repository_url"],
            "additionalProperties": False,
        }
