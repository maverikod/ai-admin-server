from ai_admin.core.custom_exceptions import CustomError, PermissionError, ValidationError
"""Default Security Adapter for AI Admin.

This module provides a concrete implementation of SecurityAdapter with
basic security functionality for testing and default operations.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from ai_admin.security.base_security_adapter import SecurityAdapter, SecurityOperation
import logging


class DefaultSecurityAdapter(SecurityAdapter):
    """Default concrete implementation of SecurityAdapter.

    This class provides basic security functionality with permissive
    defaults for testing and development purposes.
    """

    def __init__(self, settings_manager: Optional[Any] = None, roles_config: Optional[Any] = None):
        """Initialize Default Security Adapter."""
        super().__init__(settings_manager, roles_config)
        self.logger = logging.getLogger("ai_admin.default_security_adapter")

    async def validate_operation(self, operation: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate operation based on roles and permissions.

        Args:
            operation: Operation to validate
            params: Operation parameters

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.debug(f"Validating operation: {operation}")

            # Get user roles from params
            user_roles = params.get("user_roles", ["admin"])

            # Check if operation is allowed
            has_permission, missing_permissions = await self.check_permissions(user_roles, operation)

            if not has_permission:
                error_msg = f"Operation '{operation}' not allowed. Missing permissions: {missing_permissions}"
                return False, error_msg

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating operation: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    async def check_permissions(self, user_roles: List[str], operation: str) -> Tuple[bool, List[str]]:
        """
        Check if user has permissions for operation.

        Args:
            user_roles: List of user roles
            operation: Operation to check

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            self.logger.debug(f"Checking permissions for roles {user_roles} and operation {operation}")

            # Default permissive behavior - admin can do everything
            if "admin" in user_roles:
                return True, []

            # Map operations to required permissions
            operation_permissions = {
                "read": ["read", "user"],
                "write": ["write", "user"],
                "delete": ["delete", "admin"],
                "execute": ["execute", "user"],
                "admin": ["admin"],
                "system": ["admin"],
                "ssl": ["admin"],
                "certificate": ["admin"],
                "k8s": ["admin"],
                "docker": ["user"],
                "git": ["user"],
                "ftp": ["user"],
                "vast": ["admin"],
            }

            # Check if operation requires specific permissions
            required_permissions = []
            for op_type, perms in operation_permissions.items():
                if op_type in operation.lower():
                    required_permissions.extend(perms)

            if not required_permissions:
                # Default: allow user operations
                required_permissions = ["user"]

            # Check if user has any required permission
            user_permissions = self._get_user_permissions(user_roles) or []
            for perm in required_permissions:
                if perm in user_permissions:
                    return True, []

            # Return missing permissions
            missing = [p for p in required_permissions if p not in (user_permissions or [])]
            return False, missing

        except PermissionError as e:
            self.logger.error(f"Error checking permissions: {str(e)}")
            return False, ["admin"]  # Fail safe: require admin

    async def audit_operation(self, operation: str, params: Dict[str, Any], result: Any) -> None:
        """
        Audit operation for security monitoring.

        Args:
            operation: Operation that was performed
            params: Operation parameters
            result: Operation result
        """
        try:
            # Create audit record
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation,
                "user_roles": params.get("user_roles", []),
                "parameters": {k: v for k, v in params.items() if k != "user_roles"},
                "success": getattr(result, "is_success", True) if hasattr(result, "is_success") else True,
                "result_type": type(result).__name__,
            }

            # Log audit data
            self.logger.info(f"Security audit: {audit_data}")

            # Store audit data (base class method)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing operation: {str(e)}")

    def _get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """
        Get all permissions for user roles.

        Args:
            user_roles: List of user roles

        Returns:
            List of user permissions
        """
        try:
            permissions = []

            # Default role permissions
            role_permissions = {
                "admin": ["admin", "execute", "write", "read", "delete", "user"],
                "user": ["user", "read", "write", "execute"],
                "read": ["read"],
                "guest": ["read"],
            }

            for role in user_roles:
                if role in role_permissions:
                    permissions.extend(role_permissions[role])

            return list(set(permissions))  # Remove duplicates

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []
