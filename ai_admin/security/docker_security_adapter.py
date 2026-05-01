from ai_admin.core.custom_exceptions import CustomError, PermissionError, ValidationError
"""Docker Security Adapter for AI Admin.

This module provides security integration for Docker operations including
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


class DockerOperation(Enum):
    """Docker operation types."""

    BUILD = "build"
    RUN = "run"
    PUSH = "push"
    PULL = "pull"
    LOGIN = "login"
    COPY = "cp"
    EXEC = "exec"
    STOP = "stop"
    START = "start"
    RESTART = "restart"
    REMOVE = "rm"
    INSPECT = "inspect"
    LOGS = "logs"

    # Docker Hub operations
    HUB_IMAGES = "hub_images"
    HUB_IMAGE_INFO = "hub_image_info"
    HUB_SEARCH = "hub_search"

    # Docker Network operations
    NETWORK_LS = "network_ls"
    NETWORK_INSPECT = "network_inspect"
    NETWORK_CREATE = "network_create"
    NETWORK_CONNECT = "network_connect"
    NETWORK_DISCONNECT = "network_disconnect"
    NETWORK_RM = "network_rm"

    # Docker Volume operations
    VOLUME_LS = "volume_ls"
    VOLUME_CREATE = "volume_create"
    VOLUME_INSPECT = "volume_inspect"
    VOLUME_RM = "volume_rm"
    VOLUME_PRUNE = "volume_prune"

    # Docker Search operations
    SEARCH_CLI = "search_cli"

    # Docker Tag operations
    TAG = "tag"


class DockerSecurityAdapter:
    """Security adapter for Docker operations.

    This class provides:
    - Role-based access control for Docker operations
    - Operation auditing and logging
    - Permission validation for Docker resources
    - Registry access validation
    - Image permission checking
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Docker Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.docker_security")

        # Docker operation permissions mapping
        self.docker_permissions = {
            DockerOperation.BUILD: ["docker:build", "docker:admin"],
            DockerOperation.RUN: ["docker:run", "docker:admin"],
            DockerOperation.PUSH: ["docker:push", "docker:admin"],
            DockerOperation.PULL: ["docker:pull", "docker:admin"],
            DockerOperation.LOGIN: ["docker:login", "docker:admin"],
            DockerOperation.COPY: ["docker:cp", "docker:admin"],
            DockerOperation.EXEC: ["docker:exec", "docker:admin"],
            DockerOperation.STOP: ["docker:stop", "docker:admin"],
            DockerOperation.START: ["docker:start", "docker:admin"],
            DockerOperation.RESTART: ["docker:restart", "docker:admin"],
            DockerOperation.REMOVE: ["docker:rm", "docker:admin"],
            DockerOperation.INSPECT: ["docker:inspect", "docker:admin"],
            DockerOperation.LOGS: ["docker:logs", "docker:admin"],
            # Docker Hub operations
            DockerOperation.HUB_IMAGES: ["docker:hub:images", "docker:admin"],
            DockerOperation.HUB_IMAGE_INFO: ["docker:hub:info", "docker:admin"],
            DockerOperation.HUB_SEARCH: ["docker:hub:search", "docker:admin"],
            # Docker Network operations
            DockerOperation.NETWORK_LS: ["docker:network:ls", "docker:admin"],
            DockerOperation.NETWORK_INSPECT: ["docker:network:inspect", "docker:admin"],
            DockerOperation.NETWORK_CREATE: ["docker:network:create", "docker:admin"],
            DockerOperation.NETWORK_CONNECT: ["docker:network:connect", "docker:admin"],
            DockerOperation.NETWORK_DISCONNECT: [
                "docker:network:disconnect",
                "docker:admin",
            ],
            DockerOperation.NETWORK_RM: ["docker:network:rm", "docker:admin"],
            # Docker Volume operations
            DockerOperation.VOLUME_LS: ["docker:volume:ls", "docker:admin"],
            DockerOperation.VOLUME_CREATE: ["docker:volume:create", "docker:admin"],
            DockerOperation.VOLUME_INSPECT: ["docker:volume:inspect", "docker:admin"],
            DockerOperation.VOLUME_RM: ["docker:volume:rm", "docker:admin"],
            DockerOperation.VOLUME_PRUNE: ["docker:volume:prune", "docker:admin"],
            # Docker Search operations
            DockerOperation.SEARCH_CLI: ["docker:search", "docker:admin"],
            # Docker Tag operations
            DockerOperation.TAG: ["docker:tag", "docker:admin"],
        }

        # Registry access permissions
        self.registry_permissions = {
            "docker.io": ["docker:registry:docker.io"],
            "gcr.io": ["docker:registry:gcr.io"],
            "quay.io": ["docker:registry:quay.io"],
            "registry.gitlab.com": ["docker:registry:gitlab.com"],
        }

    def validate_docker_operation(
        self,
        operation: DockerOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Docker operation.

        Args:
            operation: Docker operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Docker operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.docker_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Docker operation: {operation.value}"

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
            self.audit_docker_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Docker operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_docker_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Docker permissions.

        Args:
            user_roles: List of user roles
            required_permissions: List of required permissions

        Returns:
            Tuple of (has_permission, missing_permissions)
        """
        try:
            user_permissions = self._get_user_permissions(user_roles)
            missing_permissions = []

            for permission in required_permissions:
                if permission not in user_permissions:
                    missing_permissions.append(permission)

            has_permission = len(missing_permissions) == 0

            self.logger.debug(
                f"Permission check: {has_permission}, "
                f"missing: {missing_permissions}"
            )

            return has_permission, missing_permissions

        except PermissionError as e:
            self.logger.error(f"Error checking Docker permissions: {str(e)}")
            return False, required_permissions

    def audit_docker_operation(
        self,
        operation: DockerOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Docker operation for security monitoring.

        Args:
            operation: Docker operation type
            user_roles: List of user roles
            operation_params: Operation parameters
            status: Operation status (validated, executed, failed)
        """
        try:
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation.value,
                "user_roles": user_roles,
                "status": status,
                "operation_params": operation_params or {},
            }

            # Log audit information
            self.logger.info(f"Docker operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing Docker operation: {str(e)}")

    def get_docker_roles(self) -> Dict[str, List[str]]:
        """
        Get Docker-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their Docker permissions
        """
        try:
            docker_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                docker_permissions = [
                    perm for perm in role_permissions if perm.startswith("docker:")
                ]

                if docker_permissions:
                    docker_roles[role_name] = docker_permissions

            return docker_roles

        except CustomError as e:
            self.logger.error(f"Error getting Docker roles: {str(e)}")
            return {}

    def validate_docker_registry_access(
        self, registry_url: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Docker registry.

        Args:
            registry_url: Registry URL
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Extract registry hostname
            registry_host = self._extract_registry_host(registry_url)

            # Check registry-specific permissions
            required_permissions = self.registry_permissions.get(
                registry_host, ["docker:registry:default"]
            )

            has_permission, missing_permissions = self.check_docker_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to registry {registry_host}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating registry access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_docker_image_permissions(
        self, image_name: str, operation: DockerOperation, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific Docker image operation.

        Args:
            image_name: Docker image name
            operation: Docker operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass image-specific checks)
            if self._check_user_permissions(user_roles, ["docker:admin"]):
                return True, ""

            # Check image-specific permissions
            image_permissions = self._get_image_permissions(image_name)
            if not image_permissions:
                # No specific restrictions, check general operation permissions
                return self.validate_docker_operation(operation, user_roles)

            # Check if user has required image permissions
            has_permission, missing_permissions = self.check_docker_permissions(
                user_roles, image_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to image {image_name}. Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking image permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

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

    def _validate_operation_specific_params(
        self,
        operation: DockerOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Docker operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation == DockerOperation.PUSH:
                return self._validate_push_operation(operation_params, user_roles)
            elif operation == DockerOperation.PULL:
                return self._validate_pull_operation(operation_params, user_roles)
            elif operation == DockerOperation.RUN:
                return self._validate_run_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_push_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Docker push operation parameters."""
        try:
            image_name = operation_params.get("image_name", "")
            if not image_name:
                return False, "Image name is required for push operation"

            # Check registry access
            registry_url = self._extract_registry_from_image(image_name)
            if registry_url:
                has_access, error_msg = self.validate_docker_registry_access(
                    registry_url, user_roles
                )
                if not has_access:
                    return False, error_msg

            # Check image permissions
            has_permission, error_msg = self.check_docker_image_permissions(
                image_name, DockerOperation.PUSH, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating push operation: {str(e)}"

    def _validate_pull_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Docker pull operation parameters."""
        try:
            image_name = operation_params.get("image_name", "")
            if not image_name:
                return False, "Image name is required for pull operation"

            # Check registry access
            registry_url = self._extract_registry_from_image(image_name)
            if registry_url:
                has_access, error_msg = self.validate_docker_registry_access(
                    registry_url, user_roles
                )
                if not has_access:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating pull operation: {str(e)}"

    def _validate_run_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Docker run operation parameters."""
        try:
            image_name = operation_params.get("image", "")
            if not image_name:
                return False, "Image name is required for run operation"

            # Check image permissions
            has_permission, error_msg = self.check_docker_image_permissions(
                image_name, DockerOperation.RUN, user_roles
            )
            if not has_permission:
                return False, error_msg

            # Check for privileged mode (requires admin permissions)
            privileged = operation_params.get("privileged", False)
            if privileged:
                if not self._check_user_permissions(user_roles, ["docker:admin"]):
                    return False, "Privileged mode requires admin permissions"

            return True, ""

        except ValidationError as e:
            return False, f"Error validating run operation: {str(e)}"

    def _extract_registry_host(self, registry_url: str) -> str:
        """Extract registry hostname from URL."""
        try:
            if "://" in registry_url:
                return registry_url.split("://")[1].split("/")[0]
            else:
                return registry_url.split("/")[0]
        except CustomError:
            return "unknown"

    def _extract_registry_from_image(self, image_name: str) -> Optional[str]:
        """Extract registry URL from image name."""
        try:
            if "/" in image_name:
                parts = image_name.split("/")
                if "." in parts[0] or ":" in parts[0]:
                    return parts[0]
            return None
        except CustomError:
            return None

    def _get_image_permissions(self, image_name: str) -> List[str]:
        """
        Get specific permissions required for image.

        Args:
            image_name: Docker image name

        Returns:
            List of required permissions for the image
        """
        try:
            # This could be extended to read from configuration
            # For now, return empty list (no specific restrictions)
            return []

        except PermissionError as e:
            self.logger.error(f"Error getting image permissions: {str(e)}")
            return []

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
