from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""LLM Security Adapter for AI Admin.

This module provides security integration for LLM operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class LLMOperation(Enum):
    """LLM operation types."""

    INFERENCE = "inference"
    TRAIN = "train"
    FINE_TUNE = "fine_tune"
    EVALUATE = "evaluate"
    DEPLOY = "deploy"
    SCALE = "scale"
    MONITOR = "monitor"
    LOGS = "logs"
    BACKUP = "backup"
    RESTORE = "restore"
    CONFIGURE = "configure"
    DELETE = "delete"


class LLMBackend(Enum):
    """LLM backend types."""

    LOCAL = "local"
    VAST = "vast"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class LLMSecurityAdapter:
    """Security adapter for LLM operations.

    This class provides:
    - Role-based access control for LLM operations
    - Operation auditing and logging
    - Permission validation for LLM resources
    - Model access validation
    - SSL/TLS certificate management for LLM connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize LLM Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig(roles_file="config/roles.json")
        self.logger = logging.getLogger("ai_admin.llm_security")

        # LLM operation permissions mapping
        self.llm_permissions = {
            LLMOperation.INFERENCE: ["llm:inference", "llm:admin"],
            LLMOperation.TRAIN: ["llm:train", "llm:admin"],
            LLMOperation.FINE_TUNE: ["llm:fine_tune", "llm:admin"],
            LLMOperation.EVALUATE: ["llm:evaluate", "llm:admin"],
            LLMOperation.DEPLOY: ["llm:deploy", "llm:admin"],
            LLMOperation.SCALE: ["llm:scale", "llm:admin"],
            LLMOperation.MONITOR: ["llm:monitor", "llm:admin"],
            LLMOperation.LOGS: ["llm:logs", "llm:admin"],
            LLMOperation.BACKUP: ["llm:backup", "llm:admin"],
            LLMOperation.RESTORE: ["llm:restore", "llm:admin"],
            LLMOperation.CONFIGURE: ["llm:configure", "llm:admin"],
            LLMOperation.DELETE: ["llm:delete", "llm:admin"],
        }

        # LLM backend permissions
        self.backend_permissions = {
            LLMBackend.LOCAL: ["llm:backend:local"],
            LLMBackend.VAST: ["llm:backend:vast"],
            LLMBackend.OPENAI: ["llm:backend:openai"],
            LLMBackend.ANTHROPIC: ["llm:backend:anthropic"],
            LLMBackend.COHERE: ["llm:backend:cohere"],
            LLMBackend.HUGGINGFACE: ["llm:backend:huggingface"],
        }

        # Model size permissions
        self.model_size_permissions = {
            "small": ["llm:model:small"],
            "medium": ["llm:model:medium"],
            "large": ["llm:model:large"],
            "xlarge": ["llm:model:xlarge"],
        }

    def validate_llm_operation(
        self,
        operation: LLMOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform LLM operation.

        Args:
            operation: LLM operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating LLM operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.llm_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown LLM operation: {operation.value}"

            # Check if user has required permissions
            has_permission = self._check_user_permissions(
                user_roles, required_permissions
            )
            if not has_permission:
                return (
                    False,
                    f"Insufficient permissions for operation: {operation.value}",
                )

            # Additional validation based on operation type
            if operation_params:
                validation_result = self._validate_operation_specific_params(
                    operation, operation_params, user_roles
                )
                if not validation_result[0]:
                    return validation_result

            # Audit the operation
            self.audit_llm_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating LLM operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_llm_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required LLM permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            user_permissions = self.roles_config.get_user_permissions(user_roles)
            missing_permissions = []

            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            has_permission = len(missing_permissions) == 0
            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking LLM permissions: {str(e)}")
            return False, required_permissions

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
            user_permissions = self.roles_config.get_user_permissions(user_roles)
            return any(
                permission in user_permissions for permission in required_permissions
            )
        except PermissionError as e:
            self.logger.error(f"Error checking user permissions: {str(e)}")
            return False

    def _validate_operation_specific_params(
        self,
        operation: LLMOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: LLM operation type
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate backend permissions
            backend = operation_params.get("backend")
            if backend:
                backend_enum = LLMBackend(backend)
                backend_permissions = self.backend_permissions.get(backend_enum, [])
                if backend_permissions:
                    has_backend_permission = self._check_user_permissions(
                        user_roles, backend_permissions
                    )
                    if not has_backend_permission:
                        return (
                            False,
                            f"Insufficient permissions for backend: {backend}",
                        )

            # Validate model size permissions
            model = operation_params.get("model", "")
            model_size = self._get_model_size(model)
            if model_size:
                size_permissions = self.model_size_permissions.get(model_size, [])
                if size_permissions:
                    has_size_permission = self._check_user_permissions(
                        user_roles, size_permissions
                    )
                    if not has_size_permission:
                        return (
                            False,
                            f"Insufficient permissions for model size: {model_size}",
                        )

            # Validate resource limits
            max_tokens = operation_params.get("max_tokens", 0)
            if max_tokens > 10000:  # Large token limit
                large_token_permissions = ["llm:large_tokens", "llm:admin"]
                has_large_token_permission = self._check_user_permissions(
                    user_roles, large_token_permissions
                )
                if not has_large_token_permission:
                    return (
                        False,
                        "Insufficient permissions for large token limits",
                    )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating operation parameters: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def _get_model_size(self, model: str) -> Optional[str]:
        """
        Determine model size from model name.

        Args:
            model: Model name

        Returns:
            Model size category or None
        """
        try:
            model_lower = model.lower()
            if any(size in model_lower for size in ["7b", "8b", "13b"]):
                return "small"
            elif any(size in model_lower for size in ["30b", "40b", "65b"]):
                return "medium"
            elif any(size in model_lower for size in ["70b", "80b", "100b"]):
                return "large"
            elif any(size in model_lower for size in ["175b", "200b", "300b"]):
                return "xlarge"
            return None
        except CustomError:
            return None

    def audit_llm_operation(
        self,
        operation: LLMOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit LLM operation.

        Args:
            operation: LLM operation type
            user_roles: List of user roles
            operation_params: Operation parameters
            status: Operation status
        """
        try:
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "status": status,
                "operation_params": operation_params or {},
            }

            self.logger.info(
                f"LLM operation audited: {operation.value}",
                extra={"audit_data": audit_data},
            )

        except CustomError as e:
            self.logger.error(f"Error auditing LLM operation: {str(e)}")

    def get_llm_roles(self) -> List[str]:
        """
        Get all LLM related roles.

        Returns:
            List of LLM roles
        """
        try:
            return self.roles_config.get_roles_by_category("llm")
        except CustomError as e:
            self.logger.error(f"Error getting LLM roles: {str(e)}")
            return []

    def validate_access(self, user_roles: List[str], resource: str) -> bool:
        """
        Validate access to LLM resource.

        Args:
            user_roles: List of user roles
            resource: Resource name

        Returns:
            True if access is allowed
        """
        try:
            # Check if resource is a backend
            try:
                backend = LLMBackend(resource)
                backend_permissions = self.backend_permissions.get(backend, [])
                if backend_permissions:
                    return self._check_user_permissions(user_roles, backend_permissions)
            except ValueError:
                pass

            # Check if resource is a model size
            if resource in self.model_size_permissions:
                size_permissions = self.model_size_permissions[resource]
                return self._check_user_permissions(user_roles, size_permissions)

            # Default to allowing access if no specific permissions
            return True

        except ValidationError as e:
            self.logger.error(f"Error validating access: {str(e)}")
            return False

    def check_resource_permissions(
        self, user_roles: List[str], resources: List[str]
    ) -> Dict[str, bool]:
        """
        Check permissions for multiple resources.

        Args:
            user_roles: List of user roles
            resources: List of resource names

        Returns:
            Dictionary mapping resource names to permission status
        """
        try:
            permissions = {}
            for resource in resources:
                permissions[resource] = self.validate_access(user_roles, resource)

            return permissions

        except PermissionError as e:
            self.logger.error(f"Error checking resource permissions: {str(e)}")
            return {resource: False for resource in resources}

    def manage_certificates(
        self, operation: str, user_roles: List[str], **kwargs
    ) -> Tuple[bool, str]:
        """
        Manage SSL certificates for LLM connections.

        Args:
            operation: Certificate operation (generate, validate, revoke)
            user_roles: List of user roles
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["llm:certificates", "llm:admin"]
            has_permission = self._check_user_permissions(user_roles, cert_permissions)

            if not has_permission:
                return False, "Insufficient permissions for certificate management"

            # Audit certificate operation
            self.audit_llm_operation(
                LLMOperation.CONFIGURE, user_roles, {"cert_operation": operation}
            )

            return True, "Certificate operation authorized"

        except SSLError as e:
            error_msg = f"Error managing certificates: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def setup_ssl(
        self, user_roles: List[str], backend: str, **kwargs
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for LLM connections.

        Args:
            user_roles: List of user roles
            backend: LLM backend name
            **kwargs: Additional parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["llm:ssl", "llm:admin"]
            has_permission = self._check_user_permissions(user_roles, ssl_permissions)

            if not has_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate backend access
            backend_enum = LLMBackend(backend)
            backend_permissions = self.backend_permissions.get(backend_enum, [])
            if backend_permissions:
                has_backend_permission = self._check_user_permissions(
                    user_roles, backend_permissions
                )
                if not has_backend_permission:
                    return False, f"Insufficient permissions for backend: {backend}"

            # Audit SSL setup
            self.audit_llm_operation(
                LLMOperation.CONFIGURE,
                user_roles,
                {"ssl_setup": True, "backend": backend},
            )

            return True, "SSL setup authorized"

        except ConfigurationError as e:
            error_msg = f"Error setting up SSL: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg
