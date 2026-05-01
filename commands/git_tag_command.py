from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git tag command for managing tags.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitTagCommand(BaseUnifiedCommand):
    """Manage Git tags.

    This command supports various Git tag operations including:
    - List tags
    - Create lightweight tags
    - Create annotated tags
    - Delete tags
    - Push tags to remote
    - Show tag information
    """

    name = "git_tag"

    def __init__(self):
        """Initialize Git tag command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        tag_name: Optional[str] = None,
        commit: Optional[str] = None,
        message: Optional[str] = None,
        force: bool = False,
        delete: bool = False,
        push: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git tag command with unified security.

        Args:
            action: Tag action (list, create, delete, push, show)
            tag_name: Name of the tag
            commit: Commit to tag
            message: Tag message
            force: Force operation
            delete: Delete tag
            push: Push tag to remote
            user_roles: List of user roles for security validation

        Returns:
            Success result with tag information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            tag_name=tag_name,
            commit=commit,
            message=message,
            force=force,
            delete=delete,
            push=push,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git tag command."""
        return "git:tag"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git tag command logic."""
        action = kwargs.get("action", "list")

        if action == "list":
            return await self._list_tags(**kwargs)
        elif action == "create":
            return await self._create_tag(**kwargs)
        elif action == "delete":
            return await self._delete_tag(**kwargs)
        elif action == "push":
            return await self._push_tag(**kwargs)
        elif action == "show":
            return await self._show_tag(**kwargs)
        else:
            raise CustomError(f"Unknown tag action: {action}")

    async def _list_tags(self, **kwargs) -> Dict[str, Any]:
        """List Git tags."""
        try:
            cmd = ["git", "tag", "--list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git tag list failed: {result.stderr}")

            tags = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    tags.append(line.strip())

            return {
                "message": f"Found {len(tags)} tags",
                "action": "list",
                "tags": tags,
                "count": len(tags),
                "raw_output": result.stdout,
                    "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git tag list command timed out: {str(e)}")

    async def _create_tag(
        self,
        tag_name: str,
        commit: Optional[str] = None,
        message: Optional[str] = None,
        force: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Git tag."""
        try:
            cmd = ["git", "tag"]

            if force:
                cmd.append("--force")
            if message:
                cmd.extend(["-m", message])

            cmd.append(tag_name)

            if commit:
                cmd.append(commit)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git tag create failed: {result.stderr}")

                return {
                "message": f"Created tag '{tag_name}' successfully",
                "action": "create",
                "tag_name": tag_name,
                "commit": commit,
                "message": message,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git tag create command timed out: {str(e)}")

    async def _delete_tag(
        self,
        tag_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Git tag."""
        try:
            cmd = ["git", "tag", "--delete", tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git tag delete failed: {result.stderr}")

                return {
                "message": f"Deleted tag '{tag_name}' successfully",
                "action": "delete",
                "tag_name": tag_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git tag delete command timed out: {str(e)}")

    async def _push_tag(
        self,
        tag_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Push Git tag to remote."""
        try:
            cmd = ["git", "push", "origin", tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git tag push failed: {result.stderr}")

                return {
                "message": f"Pushed tag '{tag_name}' successfully",
                "action": "push",
                "tag_name": tag_name,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git tag push command timed out: {str(e)}")

    async def _show_tag(
        self,
        tag_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git tag information."""
        try:
            cmd = ["git", "show", tag_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git tag show failed: {result.stderr}")

                return {
                "message": f"Tag information for '{tag_name}'",
                "action": "show",
                "tag_name": tag_name,
                "content": result.stdout,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git tag show command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git tag command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Tag action (list, create, delete, push, show)",
                    "default": "list",
                    "enum": ["list", "create", "delete", "push", "show"],
                },
                "tag_name": {
                    "type": "string",
                    "description": "Name of the tag",
                },
                "commit": {
                    "type": "string",
                    "description": "Commit to tag",
                },
                "message": {
                    "type": "string",
                    "description": "Tag message",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force operation",
                    "default": False,
                },
                "delete": {
                    "type": "boolean",
                    "description": "Delete tag",
                    "default": False,
                },
                "push": {
                    "type": "boolean",
                    "description": "Push tag to remote",
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

