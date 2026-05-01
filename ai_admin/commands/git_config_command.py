from ai_admin.core.custom_exceptions import ConfigurationError
"""Git config command for managing Git configuration.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitConfigCommand(BaseUnifiedCommand):
    """Manage Git configuration.

    This command supports various Git config operations including:
    - Get configuration values
    - Set configuration values
    - List all configuration
    - Remove configuration
    - Edit configuration file
    - Global vs local configuration
    """

    name = "git_config"

    def __init__(self):
        """Initialize Git config command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        action: str = "list",
        name: Optional[str] = None,
        value: Optional[str] = None,
        global_config: bool = False,
        local_config: bool = False,
        system_config: bool = False,
        file_config: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git config command with unified security.

        Args:
            action: Config action (list, get, set, unset)
            name: Configuration name
            value: Configuration value
            global_config: Use global config
            local_config: Use local config
            system_config: Use system config
            file_config: Use specific config file
            user_roles: List of user roles for security validation

        Returns:
            Success result with config information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            name=name,
            value=value,
            global_config=global_config,
            local_config=local_config,
            system_config=system_config,
            file_config=file_config,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git config command."""
        return "git:config"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git config command logic."""
        action = kwargs.get("action", "list")

        if action == "list":
            return await self._list_config(**kwargs)
        elif action == "get":
            return await self._get_config(**kwargs)
        elif action == "set":
            return await self._set_config(**kwargs)
        elif action == "unset":
            return await self._unset_config(**kwargs)
        else:
            raise ConfigurationError(f"Unknown config action: {action}")

    async def _list_config(self, **kwargs) -> Dict[str, Any]:
        """List Git configuration."""
        try:
            cmd = ["git", "config", "--list"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise ConfigurationError(f"Git config list failed: {result.stderr}")

            config_items = []
            for line in result.stdout.strip().split("\n"):
                if line.strip() and "=" in line:
                    name, value = line.split("=", 1)
                    config_items.append({"name": name.strip(), "value": value.strip()})

            return {
                "message": f"Found {len(config_items)} configuration items",
                "action": "list",
                "config_items": config_items,
                "count": len(config_items),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise ConfigurationError(f"Git config list command timed out: {str(e)}")

    async def _get_config(
        self,
        name: Optional[str] = None,
        global_config: bool = False,
        local_config: bool = False,
        system_config: bool = False,
        file_config: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Get Git configuration value."""
        try:
            # Validate required parameters
            if not name:
                raise ConfigurationError("Configuration name is required for get action")
            
            cmd = ["git", "config"]

            # Add scope options
            if global_config:
                cmd.append("--global")
            elif local_config:
                cmd.append("--local")
            elif system_config:
                cmd.append("--system")
            elif file_config:
                cmd.extend(["--file", file_config])

            cmd.append(name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise ConfigurationError(f"Git config get failed: {result.stderr}")

            return {
                "message": f"Retrieved config value for '{name}'",
                "action": "get",
                "name": name,
                "value": result.stdout.strip(),
                "global_config": global_config,
                "local_config": local_config,
                "system_config": system_config,
                "file_config": file_config,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise ConfigurationError(f"Git config get command timed out: {str(e)}")

    async def _set_config(
        self,
        name: Optional[str] = None,
        value: Optional[str] = None,
        global_config: bool = False,
        local_config: bool = False,
        system_config: bool = False,
        file_config: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Set Git configuration value."""
        try:
            # Validate required parameters
            if not name:
                raise ConfigurationError("Configuration name is required for set action")
            if value is None:
                raise ConfigurationError("Configuration value is required for set action")
            
            cmd = ["git", "config"]

            # Add scope options
            if global_config:
                cmd.append("--global")
            elif local_config:
                cmd.append("--local")
            elif system_config:
                cmd.append("--system")
            elif file_config:
                cmd.extend(["--file", file_config])

            cmd.extend([name, value])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise ConfigurationError(f"Git config set failed: {result.stderr}")

            return {
                "message": f"Set config value for '{name}'",
                "action": "set",
                "name": name,
                "value": value,
                "global_config": global_config,
                "local_config": local_config,
                "system_config": system_config,
                "file_config": file_config,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise ConfigurationError(f"Git config set command timed out: {str(e)}")

    async def _unset_config(
        self,
        name: Optional[str] = None,
        global_config: bool = False,
        local_config: bool = False,
        system_config: bool = False,
        file_config: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Unset Git configuration value."""
        try:
            # Validate required parameters
            if not name:
                raise ConfigurationError("Configuration name is required for unset action")
            
            cmd = ["git", "config", "--unset"]

            # Add scope options
            if global_config:
                cmd.append("--global")
            elif local_config:
                cmd.append("--local")
            elif system_config:
                cmd.append("--system")
            elif file_config:
                cmd.extend(["--file", file_config])

            cmd.append(name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise ConfigurationError(f"Git config unset failed: {result.stderr}")

            return {
                "message": f"Unset config value for '{name}'",
                "action": "unset",
                "name": name,
                "global_config": global_config,
                "local_config": local_config,
                "system_config": system_config,
                "file_config": file_config,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise ConfigurationError(f"Git config unset command timed out: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git config command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Config action (list, get, set, unset)",
                    "default": "list",
                    "enum": ["list", "get", "set", "unset"],
                },
                "name": {
                    "type": "string",
                    "description": "Configuration name",
                },
                "value": {
                    "type": "string",
                    "description": "Configuration value",
                },
                "global_config": {
                    "type": "boolean",
                    "description": "Use global config",
                    "default": False,
                },
                "local_config": {
                    "type": "boolean",
                    "description": "Use local config",
                    "default": False,
                },
                "system_config": {
                    "type": "boolean",
                    "description": "Use system config",
                    "default": False,
                },
                "file_config": {
                    "type": "string",
                    "description": "Use specific config file",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
