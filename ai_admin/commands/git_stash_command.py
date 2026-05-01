from ai_admin.core.custom_exceptions import CustomError
"""Git stash command for stashing changes.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitStashCommand(BaseUnifiedCommand):
    """Stash Git changes.

    This command supports various Git stash operations including:
    - Create stashes
    - List stashes
    - Apply stashes
    - Pop stashes
    - Drop stashes
    - Clear all stashes
    - Show stash contents
    """

    name = "git_stash"

    def __init__(self):
        """Initialize Git stash command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        stash_name: Optional[str] = None,
        message: Optional[str] = None,
        include_untracked: bool = False,
        include_ignored: bool = False,
        keep_index: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git stash command with unified security.

        Args:
            action: Stash action (list, create, apply, pop, drop, clear, show)
            stash_name: Name of the stash
            message: Stash message
            include_untracked: Include untracked files
            include_ignored: Include ignored files
            keep_index: Keep index
            user_roles: List of user roles for security validation

        Returns:
            Success result with stash information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            stash_name=stash_name,
            message=message,
            include_untracked=include_untracked,
            include_ignored=include_ignored,
            keep_index=keep_index,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git stash command."""
        return "git:stash"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git stash command logic."""
        action = kwargs.get("action", "list")

        if action == "list":
            return await self._list_stashes(**kwargs)
        elif action == "create":
            return await self._create_stash(**kwargs)
        elif action == "apply":
            return await self._apply_stash(**kwargs)
        elif action == "pop":
            return await self._pop_stash(**kwargs)
        elif action == "drop":
            return await self._drop_stash(**kwargs)
        elif action == "clear":
            return await self._clear_stashes(**kwargs)
        elif action == "show":
            return await self._show_stash(**kwargs)
        else:
            raise CustomError(f"Unknown stash action: {action}")

    async def _list_stashes(self, **kwargs) -> Dict[str, Any]:
        """List Git stashes."""
        try:
            cmd = ["git", "stash", "list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash list failed: {result.stderr}")

            stashes = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    stashes.append(line.strip())

            return {
                "message": f"Found {len(stashes)} stashes",
                "action": "list",
                "stashes": stashes,
                "count": len(stashes),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash list command timed out: {str(e)}")

    async def _create_stash(
        self,
        message: Optional[str] = None,
        include_untracked: bool = False,
        include_ignored: bool = False,
        keep_index: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Git stash."""
        try:
            cmd = ["git", "stash", "push"]

            if message:
                cmd.extend(["-m", message])
            if include_untracked:
                cmd.append("-u")
            if include_ignored:
                cmd.append("-a")
            if keep_index:
                cmd.append("--keep-index")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash create failed: {result.stderr}")

            return {
                "message": f"Created stash successfully",
                "action": "create",
                "message": message,
                "include_untracked": include_untracked,
                "include_ignored": include_ignored,
                "keep_index": keep_index,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash create command timed out: {str(e)}")

    async def _apply_stash(
        self,
        stash_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Apply Git stash."""
        try:
            cmd = ["git", "stash", "apply"]

            if stash_name:
                cmd.append(stash_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash apply failed: {result.stderr}")

            return {
                "message": f"Applied stash successfully",
                "action": "apply",
                "stash_name": stash_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash apply command timed out: {str(e)}")

    async def _pop_stash(
        self,
        stash_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pop Git stash."""
        try:
            cmd = ["git", "stash", "pop"]

            if stash_name:
                cmd.append(stash_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash pop failed: {result.stderr}")

            return {
                "message": f"Popped stash successfully",
                "action": "pop",
                "stash_name": stash_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash pop command timed out: {str(e)}")

    async def _drop_stash(
        self,
        stash_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Drop Git stash."""
        try:
            cmd = ["git", "stash", "drop"]

            if stash_name:
                cmd.append(stash_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash drop failed: {result.stderr}")

            return {
                "message": f"Dropped stash successfully",
                "action": "drop",
                "stash_name": stash_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash drop command timed out: {str(e)}")

    async def _clear_stashes(self, **kwargs) -> Dict[str, Any]:
        """Clear all Git stashes."""
        try:
            cmd = ["git", "stash", "clear"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash clear failed: {result.stderr}")

            return {
                "message": f"Cleared all stashes successfully",
                "action": "clear",
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash clear command timed out: {str(e)}")

    async def _show_stash(
        self,
        stash_name: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git stash contents."""
        try:
            cmd = ["git", "stash", "show"]

            if stash_name:
                cmd.append(stash_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git stash show failed: {result.stderr}")

            return {
                "message": f"Stash contents shown successfully",
                "action": "show",
                "stash_name": stash_name,
                "content": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git stash show command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git stash command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Stash action (list, create, apply, pop, drop, clear, show)",
                    "default": "list",
                    "enum": ["list", "create", "apply", "pop", "drop", "clear", "show"],
                },
                "stash_name": {
                    "type": "string",
                    "description": "Name of the stash",
                },
                "message": {
                    "type": "string",
                    "description": "Stash message",
                },
                "include_untracked": {
                    "type": "boolean",
                    "description": "Include untracked files",
                    "default": False,
                },
                "include_ignored": {
                    "type": "boolean",
                    "description": "Include ignored files",
                    "default": False,
                },
                "keep_index": {
                    "type": "boolean",
                    "description": "Keep index",
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
