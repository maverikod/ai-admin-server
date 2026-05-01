from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Queue Security Adapter for AI Admin.

This module provides security integration for Queue operations including
role-based access control, operation auditing, and permission validation.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig


class QueueOperation(Enum):
    """Queue operation types."""

    PUSH = "push"
    STATUS = "status"
    CANCEL = "cancel"
    TASK_STATUS = "task_status"
    MANAGE = "manage"
    PAUSE = "pause"
    RESUME = "resume"
    RETRY = "retry"
    CLEAR = "clear"
    LOGS = "logs"
    MONITOR = "monitor"
    CONFIGURE = "configure"


class QueueSecurityAdapter:
    """Security adapter for Queue operations.

    This class provides:
    - Role-based access control for Queue operations
    - Operation auditing and logging
    - Permission validation for Queue resources
    - Queue access validation
    - Task permission checking
    - SSL/TLS certificate management for Queue connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Queue Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.queue_security")

        # Queue operation permissions mapping
        self.queue_permissions = {
            QueueOperation.PUSH: ["queue:push", "queue:admin"],
            QueueOperation.STATUS: ["queue:status", "queue:admin"],
            QueueOperation.CANCEL: ["queue:cancel", "queue:admin"],
            QueueOperation.TASK_STATUS: ["queue:task_status", "queue:admin"],
            QueueOperation.MANAGE: ["queue:manage", "queue:admin"],
            QueueOperation.PAUSE: ["queue:pause", "queue:admin"],
            QueueOperation.RESUME: ["queue:resume", "queue:admin"],
            QueueOperation.RETRY: ["queue:retry", "queue:admin"],
            QueueOperation.CLEAR: ["queue:clear", "queue:admin"],
            QueueOperation.LOGS: ["queue:logs", "queue:admin"],
            QueueOperation.MONITOR: ["queue:monitor", "queue:admin"],
            QueueOperation.CONFIGURE: ["queue:configure", "queue:admin"],
        }

        # Queue resource permissions
        self.queue_resource_permissions = {
            "docker_tasks": ["queue:docker", "queue:admin"],
            "git_tasks": ["queue:git", "queue:admin"],
            "github_tasks": ["queue:github", "queue:admin"],
            "ollama_tasks": ["queue:ollama", "queue:admin"],
            "k8s_tasks": ["queue:k8s", "queue:admin"],
            "vast_tasks": ["queue:vast", "queue:admin"],
            "system_tasks": ["queue:system", "queue:admin"],
            "custom_tasks": ["queue:custom", "queue:admin"],
        }

    def validate_queue_operation(
        self,
        operation: QueueOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Queue operation.

        Args:
            operation: Queue operation to validate
            user_roles: List of user roles
            operation_params: Operation parameters for context

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if user has required permissions
            required_permissions = self.queue_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown queue operation: {operation.value}"

            # Validate user roles
            has_permission = self.roles_config.has_any_permission(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Insufficient permissions for queue operation: {operation.value}",
                )

            # Additional validation based on operation type
            if operation_params:
                validation_result = self._validate_operation_specific_params(
                    operation, operation_params, user_roles
                )
                if not validation_result[0]:
                    return validation_result

            # Audit the operation
            self._audit_queue_operation(operation, user_roles, operation_params)

            return True, ""

        except ValidationError as e:
            self.logger.error(f"Error validating queue operation: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def check_queue_permissions(
        self,
        user_roles: List[str],
        resource_type: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Check if user has general queue permissions.

        Args:
            user_roles: List of user roles
            resource_type: Type of queue resource to check

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check general queue permissions
            general_permissions = ["queue:read", "queue:admin"]
            has_general = self.roles_config.has_any_permission(
                user_roles, general_permissions
            )

            if not has_general:
                return False, "Insufficient general queue permissions"

            # Check resource-specific permissions if specified
            if resource_type:
                resource_permissions = self.queue_resource_permissions.get(
                    resource_type, []
                )
                if resource_permissions:
                    has_resource = self.roles_config.has_any_permission(
                        user_roles, resource_permissions
                    )
                    if not has_resource:
                        return (
                            False,
                            f"Insufficient permissions for queue resource: "
                            f"{resource_type}",
                        )

            return True, ""

        except PermissionError as e:
            self.logger.error(f"Error checking queue permissions: {str(e)}")
            return False, f"Permission check error: {str(e)}"

    def audit_queue_operation(
        self,
        operation: QueueOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
    ) -> None:
        """
        Audit Queue operation for security and compliance.

        Args:
            operation: Queue operation performed
            user_roles: List of user roles
            operation_params: Operation parameters
            result: Operation result
        """
        try:
            audit_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "operation_params": operation_params or {},
                "result": result,
                "security_level": "queue_operation",
            }

            self.logger.info(
                f"Queue operation audited: {operation.value}",
                extra={"audit_data": audit_data},
            )

            # Store audit data if configured
            if hasattr(
                self.settings_manager, "get_setting"
            ) and self.settings_manager.get_setting("audit.enabled", False):
                self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing queue operation: {str(e)}")

    def get_queue_roles(self) -> Dict[str, List[str]]:
        """
        Get available queue roles and their permissions.

        Returns:
            Dictionary mapping roles to their permissions
        """
        try:
            return {
                "queue:read": ["queue:status", "queue:task_status", "queue:logs"],
                "queue:push": ["queue:push"],
                "queue:manage": ["queue:cancel", "queue:manage", "queue:retry"],
                "queue:admin": [
                    "queue:push",
                    "queue:status",
                    "queue:cancel",
                    "queue:task_status",
                    "queue:manage",
                    "queue:pause",
                    "queue:resume",
                    "queue:retry",
                    "queue:clear",
                    "queue:logs",
                    "queue:monitor",
                    "queue:configure",
                ],
                "queue:docker": ["queue:docker_tasks"],
                "queue:git": ["queue:git_tasks"],
                "queue:github": ["queue:github_tasks"],
                "queue:ollama": ["queue:ollama_tasks"],
                "queue:k8s": ["queue:k8s_tasks"],
                "queue:vast": ["queue:vast_tasks"],
                "queue:system": ["queue:system_tasks"],
                "queue:custom": ["queue:custom_tasks"],
            }

        except CustomError as e:
            self.logger.error(f"Error getting queue roles: {str(e)}")
            return {}

    def validate_queue_access(
        self,
        user_roles: List[str],
        queue_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Validate user access to specific queue.

        Args:
            user_roles: List of user roles
            queue_name: Name of the queue to access

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Check general queue access
            has_access, error_msg = self.check_queue_permissions(user_roles)
            if not has_access:
                return has_access, error_msg

            # Check specific queue access if specified
            if queue_name:
                queue_permissions = [f"queue:{queue_name}", "queue:admin"]
                has_queue_access = self.roles_config.has_any_permission(
                    user_roles, queue_permissions
                )
                if not has_queue_access:
                    return False, f"Insufficient permissions for queue: {queue_name}"

            return True, ""

        except ValidationError as e:
            self.logger.error(f"Error validating queue access: {str(e)}")
            return False, f"Access validation error: {str(e)}"

    def check_queue_task_permissions(
        self,
        user_roles: List[str],
        task_type: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific queue task.

        Args:
            user_roles: List of user roles
            task_type: Type of task (docker, git, github, etc.)
            task_id: Task identifier

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check general task permissions
            task_permissions = ["queue:task_access", "queue:admin"]
            has_task_permission = self.roles_config.has_any_permission(
                user_roles, task_permissions
            )

            if not has_task_permission:
                return False, "Insufficient task permissions"

            # Check task-type specific permissions
            if task_type:
                type_permissions = self.queue_resource_permissions.get(
                    f"{task_type}_tasks", []
                )
                if type_permissions:
                    has_type_permission = self.roles_config.has_any_permission(
                        user_roles, type_permissions
                    )
                    if not has_type_permission:
                        return (
                            False,
                            f"Insufficient permissions for task type: {task_type}",
                        )

            return True, ""

        except PermissionError as e:
            self.logger.error(f"Error checking queue task permissions: {str(e)}")
            return False, f"Task permission check error: {str(e)}"

    def manage_queue_certificates(
        self,
        user_roles: List[str],
        operation: str,
        certificate_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Manage Queue SSL/TLS certificates.

        Args:
            user_roles: List of user roles
            operation: Certificate operation (create, update, delete, list)
            certificate_data: Certificate data for operations

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check certificate management permissions
            cert_permissions = ["queue:certificates", "queue:admin", "ssl:admin"]
            has_cert_permission = self.roles_config.has_any_permission(
                user_roles, cert_permissions
            )

            if not has_cert_permission:
                return False, "Insufficient permissions for certificate management"

            # Validate operation
            valid_operations = ["create", "update", "delete", "list", "validate"]
            if operation not in valid_operations:
                return False, f"Invalid certificate operation: {operation}"

            # Audit certificate operation
            self._audit_queue_operation(
                QueueOperation.CONFIGURE,
                user_roles,
                {
                    "certificate_operation": operation,
                    "certificate_data": certificate_data,
                },
            )

            return True, f"Certificate operation '{operation}' authorized"

        except SSLError as e:
            self.logger.error(f"Error managing queue certificates: {str(e)}")
            return False, f"Certificate management error: {str(e)}"

    def setup_queue_ssl(
        self,
        user_roles: List[str],
        ssl_config: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS for Queue connections.

        Args:
            user_roles: List of user roles
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Check SSL setup permissions
            ssl_permissions = ["queue:ssl", "queue:admin", "ssl:admin"]
            has_ssl_permission = self.roles_config.has_any_permission(
                user_roles, ssl_permissions
            )

            if not has_ssl_permission:
                return False, "Insufficient permissions for SSL setup"

            # Validate SSL configuration
            required_ssl_fields = ["cert_file", "key_file", "ca_file"]
            for field in required_ssl_fields:
                if field not in ssl_config:
                    return False, f"Missing required SSL field: {field}"

            # Audit SSL setup
            self._audit_queue_operation(
                QueueOperation.CONFIGURE,
                user_roles,
                {"ssl_setup": True, "ssl_config": ssl_config},
            )

            return True, "SSL setup authorized"

        except ConfigurationError as e:
            self.logger.error(f"Error setting up queue SSL: {str(e)}")
            return False, f"SSL setup error: {str(e)}"

    def _validate_operation_specific_params(
        self,
        operation: QueueOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Queue operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == QueueOperation.PUSH:
                # Validate push operation parameters
                task_type = operation_params.get("operation_type")
                if task_type:
                    resource_type = f"{task_type}_tasks"
                    has_resource_permission = self.roles_config.has_any_permission(
                        user_roles,
                        self.queue_resource_permissions.get(resource_type, []),
                    )
                    if not has_resource_permission:
                        return (
                            False,
                            f"Insufficient permissions for task type: {task_type}",
                        )

            elif operation == QueueOperation.MANAGE:
                # Validate manage operation parameters
                action = operation_params.get("action")
                if action in ["pause", "resume", "clear"]:
                    admin_permissions = ["queue:admin"]
                    has_admin = self.roles_config.has_any_permission(
                        user_roles, admin_permissions
                    )
                    if not has_admin:
                        return (
                            False,
                            f"Insufficient permissions for admin action: {action}",
                        )

            elif operation == QueueOperation.CANCEL:
                # Validate cancel operation parameters
                task_id = operation_params.get("task_id")
                if task_id:
                    # Check if user can cancel this specific task
                    # This could be enhanced with task ownership validation
                    pass

            return True, ""

        except ValidationError as e:
            self.logger.error(f"Error validating operation-specific params: {str(e)}")
            return False, f"Parameter validation error: {str(e)}"

    def _audit_queue_operation(
        self,
        operation: QueueOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Internal method to audit queue operations.

        Args:
            operation: Queue operation
            user_roles: List of user roles
            operation_params: Operation parameters
        """
        try:
            audit_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "operation_params": operation_params or {},
                "security_level": "queue_operation",
            }

            self.logger.info(
                f"Queue operation: {operation.value}", extra={"audit_data": audit_data}
            )

        except CustomError as e:
            self.logger.error(f"Error in queue operation audit: {str(e)}")

    def _store_audit_data(self, audit_data: Dict[str, Any]) -> None:
        """
        Store audit data for compliance.

        Args:
            audit_data: Audit data to store
        """
        try:
            # This could be implemented to store audit data in a database
            # or external audit system
            if hasattr(self.settings_manager, "get_setting"):
                audit_file = self.settings_manager.get_setting("audit.file_path")
                if audit_file:
                    import json

                    with open(audit_file, "a") as f:
                        f.write(json.dumps(audit_data) + "\n")

        except CustomError as e:
            self.logger.error(f"Error storing audit data: {str(e)}")
