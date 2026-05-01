from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, SecurityError, ValidationError
"""Base Security Adapter for AI Admin.

This module provides the base security adapter class that all specialized
security adapters inherit from, ensuring consistent security implementation
across all components.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class SecurityOperation(Enum):
    """Base security operation types."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class SecurityError(Exception):
    """Base security error exception."""

    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class SecurityAdapter(ABC):
    """Base security adapter for all command types.

    This class provides the foundation for all security adapters,
    ensuring consistent security implementation across all components.
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Base Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger(f"ai_admin.{self.__class__.__name__.lower()}")

        # Base operation permissions mapping
        self.base_permissions = {
            SecurityOperation.READ: ["read", "admin"],
            SecurityOperation.WRITE: ["write", "admin"],
            SecurityOperation.DELETE: ["delete", "admin"],
            SecurityOperation.EXECUTE: ["execute", "admin"],
            SecurityOperation.ADMIN: ["admin"],
        }

    @abstractmethod
    async def validate_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate operation based on roles and permissions.

        Args:
            operation: Operation to validate
            params: Operation parameters

        Returns:
            Tuple of (is_valid, error_message)
        """

    @abstractmethod
    async def check_permissions(
        self, user_roles: List[str], operation: str
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has permissions for operation.

        Args:
            user_roles: List of user roles
            operation: Operation to check

        Returns:
            Tuple of (has_permission, missing_permissions)
        """

    @abstractmethod
    async def audit_operation(
        self, operation: str, params: Dict[str, Any], result: Any
    ) -> None:
        """
        Audit operation for security monitoring.

        Args:
            operation: Operation that was performed
            params: Operation parameters
            result: Operation result
        """

    async def get_user_roles(self, context: Dict[str, Any]) -> List[str]:
        """
        Extract user roles from security context.

        Args:
            context: Security context containing user information

        Returns:
            List of user roles
        """
        try:
            # Default implementation - extract from context
            user_roles = context.get("user_roles", [])
            if not user_roles:
                # Try to get from user_id
                user_id = context.get("user_id")
                if user_id:
                    user_roles = await self._get_roles_for_user(user_id)

            return user_roles

        except CustomError as e:
            self.logger.error(f"Error getting user roles: {str(e)}")
            return []

    async def validate_access(self, resource: str, operation: str) -> bool:
        """
        Validate access to specific resource.

        Args:
            resource: Resource to access
            operation: Operation to perform

        Returns:
            True if access is allowed
        """
        try:
            # Get user context from current request
            context = await self._get_current_context()
            user_roles = await self.get_user_roles(context)

            # Check permissions
            has_permission, _ = await self.check_permissions(user_roles, operation)
            if not has_permission:
                return False

            # Check resource-specific permissions
            has_resource_access = await self.check_resource_permissions(
                user_roles, resource
            )

            return has_resource_access

        except ValidationError as e:
            self.logger.error(f"Error validating access: {str(e)}")
            return False

    async def check_resource_permissions(
        self, user_roles: List[str], resource: str
    ) -> bool:
        """
        Check permissions for specific resource.

        Args:
            user_roles: List of user roles
            resource: Resource to check

        Returns:
            True if user has access to resource
        """
        try:
            # Get resource-specific permissions
            resource_permissions = await self._get_resource_permissions(resource)

            # Check if user has any of the required permissions
            user_permissions = self._get_user_permissions(user_roles)

            for permission in resource_permissions:
                if permission in user_permissions:
                    return True

            return False

        except PermissionError as e:
            self.logger.error(f"Error checking resource permissions: {str(e)}")
            return False

    async def manage_certificates(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manage certificates for operation.

        Args:
            operation: Certificate operation
            params: Operation parameters

        Returns:
            Operation result
        """
        try:
            self.logger.info(f"Managing certificates for operation: {operation}")

            # Validate certificate operation
            has_permission, error_msg = await self.check_permissions(
                await self.get_user_roles(params), f"certificate:{operation}"
            )
            if not has_permission:
                raise SecurityError(error_msg, "CERTIFICATE_PERMISSION_DENIED")

            # Perform certificate operation
            result = await self._perform_certificate_operation(operation, params)

            # Audit the operation
            await self.audit_operation(f"certificate:{operation}", params, result)

            return result

        except SSLError as e:
            self.logger.error(f"Error managing certificates: {str(e)}")
            raise SecurityError(str(e), "CERTIFICATE_ERROR")

    async def setup_ssl(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Setup SSL configuration for operation.

        Args:
            config: SSL configuration

        Returns:
            SSL setup result
        """
        try:
            self.logger.info("Setting up SSL configuration")

            # Validate SSL setup permissions
            context = await self._get_current_context()
            user_roles = await self.get_user_roles(context)

            has_permission, error_msg = await self.check_permissions(
                user_roles, "ssl:setup"
            )
            if not has_permission:
                raise SecurityError(error_msg, "SSL_PERMISSION_DENIED")

            # Setup SSL
            result = await self._perform_ssl_setup(config)

            # Audit the operation
            await self.audit_operation("ssl:setup", config, result)

            return result

        except ConfigurationError as e:
            self.logger.error(f"Error setting up SSL: {str(e)}")
            raise SecurityError(str(e), "SSL_ERROR")

    def _check_user_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> bool:
        """
        Check if user has any of the required permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            True if user has at least one required permission
        """
        try:
            user_permissions = self._get_user_permissions(user_roles)

            for permission in required_permissions:
                if permission in user_permissions:
                    return True

            return False

        except PermissionError as e:
            self.logger.error(f"Error checking user permissions: {str(e)}")
            return False

    def _get_user_permissions(self, user_roles: List[str]) -> List[str]:
        """
        Get all permissions for user roles.

        Args:
            user_roles: List of user roles

        Returns:
            List of user permissions
        """
        try:
            all_permissions = []

            for role in user_roles:
                role_config = self.roles_config.get_role_config(role)
                if role_config:
                    role_permissions = role_config.get("permissions", [])
                    all_permissions.extend(role_permissions)

            return list(set(all_permissions))  # Remove duplicates

        except PermissionError as e:
            self.logger.error(f"Error getting user permissions: {str(e)}")
            return []

    async def _get_roles_for_user(self, user_id: str) -> List[str]:
        """
        Get roles for specific user.

        Args:
            user_id: User identifier

        Returns:
            List of user roles
        """
        try:
            # This could be extended to query user database
            # For now, return default roles
            return ["user"]

        except CustomError as e:
            self.logger.error(f"Error getting roles for user: {str(e)}")
            return []

    async def _get_current_context(self) -> Dict[str, Any]:
        """
        Get current security context.

        Returns:
            Current security context
        """
        try:
            # This could be extended to get from request context
            # For now, return empty context
            return {}

        except CustomError as e:
            self.logger.error(f"Error getting current context: {str(e)}")
            return {}

    async def _get_resource_permissions(self, resource: str) -> List[str]:
        """
        Get permissions required for specific resource.

        Args:
            resource: Resource identifier

        Returns:
            List of required permissions
        """
        try:
            # This could be extended to read from configuration
            # For now, return basic permissions
            return ["read", "write"]

        except PermissionError as e:
            self.logger.error(f"Error getting resource permissions: {str(e)}")
            return []

    async def _perform_certificate_operation(
        self, operation: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform certificate operation.

        Args:
            operation: Certificate operation
            params: Operation parameters

        Returns:
            Operation result
        """
        try:
            # This should be implemented by specialized adapters
            return {"status": "success", "operation": operation}

        except SSLError as e:
            self.logger.error(f"Error performing certificate operation: {str(e)}")
            raise

    async def _perform_ssl_setup(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform SSL setup.

        Args:
            config: SSL configuration

        Returns:
            SSL setup result
        """
        try:
            # This should be implemented by specialized adapters
            return {"status": "success", "ssl_configured": True}

        except CustomError as e:
            self.logger.error(f"Error performing SSL setup: {str(e)}")
            raise

    def _store_audit_data(self, audit_data: Dict[str, Any]) -> None:
        """
        Store audit data for security monitoring.

        Args:
            audit_data: Audit data to store
        """
        try:
            # This could be extended to write to database or external system
            # For now, just log the data
            self.logger.info(f"Audit data stored: {audit_data}")

        except CustomError as e:
            self.logger.error(f"Error storing audit data: {str(e)}")
