from ai_admin.core.custom_exceptions import CustomError
"""Git branch command for managing branches.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitBranchCommand(BaseUnifiedCommand):
    """Manage Git branches.

    This command supports various Git branch operations including:
    - List branches
    - Create new branches
    - Delete branches
    - Rename branches
    - Set upstream
    """

    name = "git_branch"

    def __init__(self):
        """Initialize Git branch command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        branch_name: Optional[str] = None,
        start_point: Optional[str] = None,
        force: bool = False,
        delete: bool = False,
        rename: bool = False,
        new_name: Optional[str] = None,
        set_upstream: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git branch command with unified security.

        Args:
            action: Branch action (list, create, delete, rename)
            branch_name: Name of the branch
            start_point: Starting point for new branch
            force: Force operation
            delete: Delete branch
            rename: Rename branch
            new_name: New name for branch
            set_upstream: Set upstream branch
            user_roles: List of user roles for security validation

        Returns:
            Success result with branch information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            branch_name=branch_name,
            start_point=start_point,
            force=force,
            delete=delete,
            rename=rename,
            new_name=new_name,
            set_upstream=set_upstream,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git branch command."""
        return "git:branch"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git branch command logic."""
        action = kwargs.get("action", "list")

        if action == "list":
            return await self._list_branches(**kwargs)
        elif action == "create":
            return await self._create_branch(**kwargs)
        elif action == "delete":
            return await self._delete_branch(**kwargs)
        elif action == "rename":
            return await self._rename_branch(**kwargs)
        else:
            raise CustomError(f"Unknown branch action: {action}")

    async def _list_branches(self, **kwargs) -> Dict[str, Any]:
        """List Git branches."""
        try:
            cmd = ["git", "branch", "--list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git branch list failed: {result.stderr}")

            branches = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    branch_info = line.strip()
                    is_current = branch_info.startswith("*")
                    branch_name = branch_info.lstrip("* ").strip()
                    branches.append({
                        "name": branch_name,
                        "current": is_current,
                        "raw": branch_info,
                    })

            return {
                "message": f"Found {len(branches)} branches",
                "action": "list",
                "branches": branches,
                "count": len(branches),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git branch list command timed out: {str(e)}")

    async def _create_branch(
        self,
        branch_name: str,
        start_point: Optional[str] = None,
        force: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create Git branch."""
        try:
            cmd = ["git", "branch"]

            if force:
                cmd.append("--force")

            if start_point:
                cmd.extend([start_point, branch_name])
            else:
                cmd.append(branch_name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git branch create failed: {result.stderr}")

            return {
                "message": f"Created branch '{branch_name}'",
                "action": "create",
                "branch_name": branch_name,
                "start_point": start_point,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git branch create command timed out: {str(e)}")

    async def _delete_branch(
        self,
        branch_name: str,
        force: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete Git branch."""
        try:
            cmd = ["git", "branch"]

            if force:
                cmd.append("--force")

            cmd.extend(["--delete", branch_name])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git branch delete failed: {result.stderr}")

            return {
                "message": f"Deleted branch '{branch_name}'",
                "action": "delete",
                "branch_name": branch_name,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git branch delete command timed out: {str(e)}")

    async def _rename_branch(
        self,
        branch_name: str,
        new_name: str,
        force: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Rename Git branch."""
        try:
            cmd = ["git", "branch"]

            if force:
                cmd.append("--force")

            cmd.extend(["--move", branch_name, new_name])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise CustomError(f"Git branch rename failed: {result.stderr}")

            return {
                "message": f"Renamed branch '{branch_name}' to '{new_name}'",
                "action": "rename",
                "branch_name": branch_name,
                "new_name": new_name,
                "force": force,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git branch rename command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git branch command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Branch action (list, create, delete, rename)",
                    "default": "list",
                    "enum": ["list", "create", "delete", "rename"],
                },
                "branch_name": {
                    "type": "string",
                    "description": "Name of the branch",
                },
                "start_point": {
                    "type": "string",
                    "description": "Starting point for new branch",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force operation",
                    "default": False,
                },
                "delete": {
                    "type": "boolean",
                    "description": "Delete branch",
                    "default": False,
                },
                "rename": {
                    "type": "boolean",
                    "description": "Rename branch",
                    "default": False,
                },
                "new_name": {
                    "type": "string",
                    "description": "New name for branch",
                },
                "set_upstream": {
                    "type": "string",
                    "description": "Set upstream branch",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
