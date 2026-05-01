from mcp_proxy_adapter.commands.result import SuccessResult

from ai_admin.core.custom_exceptions import ConfigurationError, CustomError

"""Example command that demonstrates dependency injection.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


from typing import Dict, Any, Optional, List

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.dependency_injection import (
    get_config,
    get_settings_manager,
    get_security_integration,
)


class ExampleDICommand:
    """Example command that demonstrates dependency injection."""

    name = "example_di"

    def __init__(self):
        """Initialize example DI command."""
        super().__init__()
        self.config = get_config()
        self.settings_manager = get_settings_manager()
        self.security_integration = get_security_integration()

    async def execute(
        self,
        action: str = "info",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute example DI command with unified security.

        Args:
            action: Action to perform (info, test, validate)
            user_roles: List of user roles for security validation

        Returns:
            Success result with action information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for example DI command."""
        return "example:di"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute example DI command logic."""
        action = kwargs.get("action", "info")

        if action == "info":
            return await self._show_info()
        elif action == "test":
            return await self._test_dependencies()
        elif action == "validate":
            return await self._validate_dependencies()
        else:
            raise CustomError(f"Unknown action: {action}")

    async def _show_info(self) -> Dict[str, Any]:
        """Show dependency injection information."""
        return {
            "message": "Dependency injection example command",
            "action": "info",
            "dependencies": {
                "config": "loaded" if self.config else "not loaded",
                "settings_manager": "loaded" if self.settings_manager else "not loaded",
                "security_integration": (
                    "loaded" if self.security_integration else "not loaded"
                ),
            },
            "config_keys": list(self.config.keys()) if self.config else [],
        }

    async def _test_dependencies(self) -> Dict[str, Any]:
        """Test dependency injection functionality."""
        results = {}

        # Test config
        try:
            if self.config:
                results["config"] = {"status": "ok", "keys": len(self.config)}
            else:
                results["config"] = {"status": "error", "message": "Config not loaded"}
        except ConfigurationError as e:
            results["config"] = {"status": "error", "message": str(e)}

        # Test settings manager
        try:
            if self.settings_manager:
                results["settings_manager"] = {
                    "status": "ok",
                    "type": type(self.settings_manager).__name__,
                }
            else:
                results["settings_manager"] = {
                    "status": "error",
                    "message": "Settings manager not loaded",
                }
        except ConfigurationError as e:
            results["settings_manager"] = {"status": "error", "message": str(e)}

        # Test security integration
        try:
            if self.security_integration:
                results["security_integration"] = {
                    "status": "ok",
                    "type": type(self.security_integration).__name__,
                }
            else:
                results["security_integration"] = {
                    "status": "error",
                    "message": "Security integration not loaded",
                }
        except CustomError as e:
            results["security_integration"] = {"status": "error", "message": str(e)}

        return {
            "message": "Dependency injection test completed",
            "action": "test",
            "results": results,
        }

    async def _validate_dependencies(self) -> Dict[str, Any]:
        """Validate dependency injection setup."""
        validation_results = {}

        # Validate config
        validation_results["config"] = {
            "required": True,
            "loaded": self.config is not None,
            "valid": bool(self.config and isinstance(self.config, dict)),
        }

        # Validate settings manager
        validation_results["settings_manager"] = {
            "required": True,
            "loaded": self.settings_manager is not None,
            "valid": self.settings_manager is not None,
        }

        # Validate security integration
        validation_results["security_integration"] = {
            "required": True,
            "loaded": self.security_integration is not None,
            "valid": self.security_integration is not None,
        }

        all_valid = all(result["valid"] for result in validation_results.values())

        return {
            "message": f"Dependency validation {'passed' if all_valid else 'failed'}",
            "action": "validate",
            "all_valid": all_valid,
            "validation_results": validation_results,
        }

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for example DI command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform (info, test, validate)",
                    "default": "info",
                    "enum": ["info", "test", "validate"],
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }


"""Module description."""
