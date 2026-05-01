from ai_admin.core.custom_exceptions import CustomError
"""Git init command for initializing repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitInitCommand(BaseUnifiedCommand):
    """Initialize Git repository.

    This command supports various Git init operations including:
    - Initialize new repository
    - Bare repository
    - Shared repository
    - Template directory
    """

    name = "git_init"

    def __init__(self):
        """Initialize Git init command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        repository_path: Optional[str] = None,
        bare: bool = False,
        shared: Optional[str] = None,
        template: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git init command with unified security.

        Args:
            repository_path: Path for the new repository
            bare: Create bare repository
            shared: Set repository sharing permissions
            template: Template directory
            quiet: Quiet mode
            verbose: Verbose mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with init information
        """
        # Use unified security approach
        return await super().execute(
            repository_path=repository_path,
            bare=bare,
            shared=shared,
            template=template,
            quiet=quiet,
            verbose=verbose,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git init command."""
        return "git:init"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git init command logic."""
        return await self._init_repository(**kwargs)

    async def _init_repository(
        self,
        repository_path: Optional[str] = None,
        bare: bool = False,
        shared: Optional[str] = None,
        template: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Initialize Git repository."""
        try:
            # Build Git command
            cmd = ["git", "init"]

            # Add options
            if bare:
                cmd.append("--bare")
            if shared:
                cmd.extend(["--shared", shared])
            if template:
                cmd.extend(["--template", template])
            if quiet:
                cmd.append("--quiet")
            if verbose:
                cmd.append("--verbose")

            # Add repository path if specified
            if repository_path:
                cmd.append(repository_path)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git init failed: {result.stderr}")

            return {
                "message": f"Git repository initialized successfully",
                "repository_path": repository_path,
                "bare": bare,
                "shared": shared,
                "template": template,
                "quiet": quiet,
                "verbose": verbose,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git init command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git init failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git init command parameters."""
        return {
            "type": "object",
            "properties": {
                "repository_path": {
                    "type": "string",
                    "description": "Path for the new repository",
                },
                "bare": {
                    "type": "boolean",
                    "description": "Create bare repository",
                    "default": False,
                },
                "shared": {
                    "type": "string",
                    "description": "Set repository sharing permissions",
                },
                "template": {
                    "type": "string",
                    "description": "Template directory",
                },
                "quiet": {
                    "type": "boolean",
                    "description": "Quiet mode",
                    "default": False,
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Verbose mode",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
