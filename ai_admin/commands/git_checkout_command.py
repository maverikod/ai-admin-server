from ai_admin.core.custom_exceptions import CustomError
"""Git checkout command for switching branches and commits.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitCheckoutCommand(BaseUnifiedCommand):
    """Checkout Git branches, commits, or files.

    This command supports various Git checkout operations including:
    - Switch to existing branch
    - Create and switch to new branch
    - Checkout specific commit
    - Checkout specific file
    - Detached HEAD mode
    """

    name = "git_checkout"

    def __init__(self):
        """Initialize Git checkout command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        target: str,
        create_branch: bool = False,
        force: bool = False,
        files: Optional[List[str]] = None,
        repository_path: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git checkout command with unified security.

        Args:
            target: Branch, commit, or file to checkout
            create_branch: Create new branch
            force: Force checkout
            files: List of files to checkout
            repository_path: Path to repository
            user_roles: List of user roles for security validation

        Returns:
            Success result with checkout information
        """
        # Validate inputs
        if not target:
            return ErrorResult(message="Target is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            target=target,
            create_branch=create_branch,
            force=force,
            files=files,
            repository_path=repository_path,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git checkout command."""
        return "git:checkout"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git checkout command logic."""
        return await self._checkout(**kwargs)

    async def _checkout(
        self,
        target: str,
        create_branch: bool = False,
        force: bool = False,
        files: Optional[List[str]] = None,
        repository_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Checkout Git target."""
        try:
            # Build Git command
            cmd = ["git", "checkout"]

            # Add options
            if create_branch:
                cmd.append("-b")
            if force:
                cmd.append("--force")

            # Add target
            cmd.append(target)

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git checkout failed: {result.stderr}")

            return {
                "message": f"Checked out '{target}'",
                "target": target,
                "create_branch": create_branch,
                "force": force,
                "files": files,
                "repository_path": repository_path,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git checkout command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git checkout failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git checkout command parameters."""
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Branch, commit, or file to checkout",
                },
                "create_branch": {
                    "type": "boolean",
                    "description": "Create new branch",
                    "default": False,
                },
                "force": {
                    "type": "boolean",
                    "description": "Force checkout",
                    "default": False,
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to checkout",
                },
                "repository_path": {
                    "type": "string",
                    "description": "Path to repository",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["target"],
            "additionalProperties": False,
        }
