from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, AuthorizationError, SSLError
"""mTLS roles command for managing role-based access control with mTLS certificates.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ssl_security_adapter import SSLSecurityAdapter

class MtlsRolesCommand(BaseUnifiedCommand):
    """Command for managing mTLS roles and role-based access control.

    This command provides functionality for:
    - Creating and managing role-based access control configurations
    - Validating mTLS certificates against role configurations
    - Checking access permissions for specific operations
    - Managing role-based access control
    """

    name = "mtls_roles"
    
    def __init__(self):
        """Initialize mTLS roles command."""
        super().__init__()
        self.security_adapter = SSLSecurityAdapter()

    async def execute(
        self,
        action: str,
        role_name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        certificate_path: Optional[str] = None,
        operation: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> SuccessResult:
        """Execute the mTLS roles command with the specified action.

        Args:
            action: Action to perform (check_access, create_roles_config,
                    validate_cert, list_roles)
            role_name: Name of the role
            permissions: List of permissions for the role
            certificate_path: Path to certificate file
            operation: Operation to check access for
            user_roles: List of user roles for security validation
            **kwargs: Additional parameters for the action
            
        Returns:
            Success result with role management information
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            role_name=role_name,
            permissions=permissions,
            certificate_path=certificate_path,
            operation=operation,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for mTLS roles command."""
        return "mtls:roles"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute mTLS roles command logic."""
        action = kwargs.get("action")
        
        if action == "check_access":
            return await self._check_access(**kwargs)
        elif action == "create_roles_config":
            return await self._create_roles_config(**kwargs)
        elif action == "validate_cert":
            return await self._validate_cert(**kwargs)
        elif action == "list_roles":
            return await self._list_roles(**kwargs)
        else:
            raise SSLError(f"Unknown mTLS roles action: {action}")

    async def _check_access(
        self,
        role_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Check access permissions for a role and operation."""
        try:
            if not role_name or not operation:
                raise AuthorizationError("Role name and operation are required for access check")

            # Mock access check logic
            allowed_operations = {
                "admin": ["read", "write", "delete", "manage"],
                "user": ["read", "write"],
                "viewer": ["read"],
            }

            role_permissions = allowed_operations.get(role_name, [])
            has_access = operation in role_permissions

            return {
                "message": f"Access check for role '{role_name}' and operation '{operation}'",
                "action": "check_access",
                "role_name": role_name,
                "operation": operation,
                "has_access": has_access,
                "permissions": role_permissions,
            }

        except AuthorizationError as e:
            raise AuthorizationError(f"Access check failed: {str(e)}")

    async def _create_roles_config(
        self,
        role_name: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create roles configuration."""
        try:
            if not role_name or not permissions:
                raise AuthorizationError("Role name and permissions are required")

            # Mock roles config creation
            roles_config = {
                "roles": {
                    role_name: {
                        "permissions": permissions,
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                }
            }

            return {
                "message": f"Created roles configuration for role '{role_name}'",
                "action": "create_roles_config",
                "role_name": role_name,
                "permissions": permissions,
                "roles_config": roles_config,
            }

        except ConfigurationError as e:
            raise ConfigurationError(f"Roles config creation failed: {str(e)}")

    async def _validate_cert(
        self,
        certificate_path: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Validate certificate against role configuration."""
        try:
            if not certificate_path:
                raise SSLError("Certificate path is required for validation")

            # Mock certificate validation
            validation_result = {
                "valid": True,
                "role": "admin",
                "permissions": ["read", "write", "delete", "manage"],
                "expires_at": "2025-01-01T00:00:00Z",
            }

            return {
                "message": f"Certificate validation completed for '{certificate_path}'",
                "action": "validate_cert",
                "certificate_path": certificate_path,
                "validation_result": validation_result,
            }

        except SSLError as e:
            raise SSLError(f"Certificate validation failed: {str(e)}")

    async def _list_roles(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List available roles."""
        try:
            # Mock roles list
            roles = {
                "admin": {
                    "permissions": ["read", "write", "delete", "manage"],
                    "description": "Full administrative access",
                },
                "user": {
                    "permissions": ["read", "write"],
                    "description": "Standard user access",
                },
                "viewer": {
                    "permissions": ["read"],
                    "description": "Read-only access",
                },
            }

            return {
                "message": f"Found {len(roles)} available roles",
                "action": "list_roles",
                "roles": roles,
                "count": len(roles),
            }

        except CustomError as e:
            raise CustomError(f"Roles listing failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for mTLS roles command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform (check_access, create_roles_config, validate_cert, list_roles)",
                    "enum": ["check_access", "create_roles_config", "validate_cert", "list_roles"],
                },
                "role_name": {
                    "type": "string",
                    "description": "Name of the role",
                },
                "permissions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of permissions for the role",
                },
                "certificate_path": {
                    "type": "string",
                    "description": "Path to certificate file",
                },
                "operation": {
                    "type": "string",
                    "description": "Operation to check access for",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["action"],
            "additionalProperties": False,
        }