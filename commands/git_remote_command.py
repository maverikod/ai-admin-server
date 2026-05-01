from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git remote command for managing remote repositories.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitRemoteCommand(BaseUnifiedCommand):
    """Manage Git remote repositories.

    This command supports various Git remote operations including:
    - List remotes
    - Add remotes
    - Remove remotes
    - Rename remotes
    - Set URL
    - Show remote details
    """

    name = "git_remote"

    def __init__(self):
        """Initialize Git remote command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        remote_name: Optional[str] = None,
        remote_url: Optional[str] = None,
        new_name: Optional[str] = None,
        fetch: bool = False,
        push: bool = False,
        all: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git remote command with unified security.

        Args:
            action: Remote action (list, add, remove, rename, set-url, show)
            remote_name: Name of the remote
            remote_url: URL of the remote
            new_name: New name for remote
            fetch: Show fetch URL
            push: Show push URL
            all: Show all remotes
            user_roles: List of user roles for security validation

        Returns:
            Success result with remote information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            remote_name=remote_name,
            remote_url=remote_url,
            new_name=new_name,
            fetch=fetch,
            push=push,
            all=all,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git remote command."""
        return "git:remote"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git remote command logic."""
        action = kwargs.get("action", "list")

        if action == "list":
            return await self._list_remotes(**kwargs)
        elif action == "add":
            return await self._add_remote(**kwargs)
        elif action == "remove":
            return await self._remove_remote(**kwargs)
        elif action == "rename":
            return await self._rename_remote(**kwargs)
        elif action == "set-url":
            return await self._set_url(**kwargs)
        elif action == "show":
            return await self._show_remote(**kwargs)
        else:
            raise CustomError(f"Unknown remote action: {action}")

    async def _list_remotes(self, **kwargs) -> Dict[str, Any]:
        """List Git remotes."""
        try:
            cmd = ["git", "remote", "-v"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote list failed: {result.stderr}")

            remotes = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        remotes.append({
                            "name": parts[0],
                            "url": parts[1],
                            "type": parts[2] if len(parts) > 2 else "fetch",
                        })

            return {
                "message": f"Found {len(remotes)} remotes",
                "action": "list",
                "remotes": remotes,
                "count": len(remotes),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote list command timed out: {str(e)}")

    async def _add_remote(
        self,
        remote_name: str,
        remote_url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Add Git remote."""
        try:
            cmd = ["git", "remote", "add", remote_name, remote_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote add failed: {result.stderr}")

            return {
                "message": f"Added remote '{remote_name}'",
                "action": "add",
                    "remote_name": remote_name,
                    "remote_url": remote_url,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote add command timed out: {str(e)}")

    async def _remove_remote(
        self,
        remote_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Remove Git remote."""
        try:
            cmd = ["git", "remote", "remove", remote_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote remove failed: {result.stderr}")

            return {
                "message": f"Removed remote '{remote_name}'",
                "action": "remove",
                "remote_name": remote_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote remove command timed out: {str(e)}")

    async def _rename_remote(
        self,
        remote_name: str,
        new_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Rename Git remote."""
        try:
            cmd = ["git", "remote", "rename", remote_name, new_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote rename failed: {result.stderr}")

            return {
                "message": f"Renamed remote '{remote_name}' to '{new_name}'",
                "action": "rename",
                "remote_name": remote_name,
                    "new_name": new_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote rename command timed out: {str(e)}")

    async def _set_url(
        self,
        remote_name: str,
        remote_url: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Set Git remote URL."""
        try:
            cmd = ["git", "remote", "set-url", remote_name, remote_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote set-url failed: {result.stderr}")

            return {
                "message": f"Set URL for remote '{remote_name}'",
                "action": "set-url",
                "remote_name": remote_name,
                "remote_url": remote_url,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote set-url command timed out: {str(e)}")

    async def _show_remote(
        self,
        remote_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git remote details."""
        try:
            cmd = ["git", "remote", "show", remote_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git remote show failed: {result.stderr}")

            return {
                "message": f"Remote details for '{remote_name}'",
                "action": "show",
                "remote_name": remote_name,
                "details": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git remote show command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git remote command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Remote action (list, add, remove, rename, set-url, show)",
                    "default": "list",
                    "enum": ["list", "add", "remove", "rename", "set-url", "show"],
                },
                "remote_name": {
                    "type": "string",
                    "description": "Name of the remote",
                },
                "remote_url": {
                    "type": "string",
                    "description": "URL of the remote",
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for remote",
                },
                "fetch": {
                    "type": "boolean",
                    "description": "Show fetch URL",
                    "default": False,
                },
                "push": {
                    "type": "boolean",
                    "description": "Show push URL",
                    "default": False,
                },
                "all": {
                    "type": "boolean",
                    "description": "Show all remotes",
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
