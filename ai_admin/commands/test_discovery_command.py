from ai_admin.core.custom_exceptions import CustomError
"""Test command for discovery verification.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.test_security_adapter import TestSecurityAdapter, TestOperation

class TestDiscoveryCommand(BaseUnifiedCommand):
    """Test command to verify auto-discovery."""

    name = "test_discovery"

    def _get_default_operation(self) -> str:
        """Get default operation name for TestDiscoveryCommand."""
        return "testdiscovery:execute"

    def __init__(self):
        """Initialize test discovery command."""
        self.security_adapter = TestSecurityAdapter()

    async def execute(self, **kwargs) -> SuccessResult:
        """Execute test discovery command.

        Args:
            **kwargs: Additional parameters

        Returns:
            SuccessResult: Test result
        """
        try:
            # Get user roles from kwargs (passed by security framework)
            user_roles = kwargs.get("user_roles", ["default"])

            # Validate operation with security adapter
            operation_params = {
                "test_path": kwargs.get("test_path"),
                "framework": kwargs.get("framework"),
                "environment": kwargs.get("environment"),
            }

            is_valid, error_msg = self.security_adapter.validate_test_operation(
                TestOperation.DISCOVERY, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_ERROR",
                    details={"operation": "discovery", "user_roles": user_roles},
                )

            return SuccessResult(
                data={
                    "message": "Test discovery command executed successfully",
                    "command_name": self.name,
                    "discovery_working": True,
                    "timestamp": "2025-08-12T21:05:00Z",
                }
            )

        except CustomError as e:
            return ErrorResult(
                message="Test discovery failed: {str(e)}", code="TEST_DISCOVERY_ERROR", details={"error": str(e)}
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters.

        Returns:
            Dict[str]: JSON schema
        """
        return {"type": "object", "properties": {}, "additionalProperties": True}
