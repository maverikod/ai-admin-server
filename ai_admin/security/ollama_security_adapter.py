from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, ValidationError
"""Ollama Security Adapter for AI Admin.

This module provides security integration for Ollama operations including
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


class OllamaOperation(Enum):
    """Ollama operation types."""

    MODELS_LIST = "models_list"
    MODELS_PULL = "models_pull"
    MODELS_REMOVE = "models_remove"
    MODELS_RUN = "models_run"
    MODELS_INFO = "models_info"
    RUN_INFERENCE = "run_inference"
    STATUS_CHECK = "status_check"
    MEMORY_STATUS = "memory_status"
    MEMORY_UNLOAD = "memory_unload"
    MEMORY_UNLOAD_ALL = "memory_unload_all"
    API_ACCESS = "api_access"
    MODEL_ACCESS = "model_access"


class OllamaSecurityAdapter:
    """Security adapter for Ollama operations.

    This class provides:
    - Role-based access control for Ollama operations
    - Operation auditing and logging
    - Permission validation for Ollama resources
    - API access validation
    - Model permission checking
    - SSL/TLS certificate management for Ollama connections
    """

    def __init__(
        self,
        settings_manager: Optional[Any] = None,
        roles_config: Optional[RolesConfig] = None,
    ):
        """
        Initialize Ollama Security Adapter.

        Args:
            settings_manager: Settings manager instance
            roles_config: Roles configuration instance
        """
        self.settings_manager = settings_manager or get_settings_manager()
        self.roles_config = roles_config or RolesConfig()
        self.logger = logging.getLogger("ai_admin.ollama_security")

        # Ollama operation permissions mapping
        self.ollama_permissions = {
            OllamaOperation.MODELS_LIST: ["ollama:models:list", "ollama:admin"],
            OllamaOperation.MODELS_PULL: ["ollama:models:pull", "ollama:admin"],
            OllamaOperation.MODELS_REMOVE: ["ollama:models:remove", "ollama:admin"],
            OllamaOperation.MODELS_RUN: ["ollama:models:run", "ollama:admin"],
            OllamaOperation.MODELS_INFO: ["ollama:models:info", "ollama:admin"],
            OllamaOperation.RUN_INFERENCE: ["ollama:inference:run", "ollama:admin"],
            OllamaOperation.STATUS_CHECK: ["ollama:status:check", "ollama:admin"],
            OllamaOperation.MEMORY_STATUS: ["ollama:memory:status", "ollama:admin"],
            OllamaOperation.MEMORY_UNLOAD: ["ollama:memory:unload", "ollama:admin"],
            OllamaOperation.MEMORY_UNLOAD_ALL: [
                "ollama:memory:unload_all",
                "ollama:admin",
            ],
            OllamaOperation.API_ACCESS: ["ollama:api:access", "ollama:admin"],
            OllamaOperation.MODEL_ACCESS: ["ollama:model:access", "ollama:admin"],
        }

        # Ollama API access permissions
        self.api_permissions = {
            "localhost": ["ollama:api:local"],
            "127.0.0.1": ["ollama:api:local"],
            "default": ["ollama:api:default"],
        }

        # Model access permissions
        self.model_permissions = {
            "llama2": ["ollama:model:llama2", "ollama:model:premium"],
            "llama3": ["ollama:model:llama3", "ollama:model:premium"],
            "codellama": ["ollama:model:codellama", "ollama:model:premium"],
            "mistral": ["ollama:model:mistral", "ollama:model:premium"],
            "gemma": ["ollama:model:gemma", "ollama:model:premium"],
            "phi": ["ollama:model:phi", "ollama:model:standard"],
            "tinyllama": ["ollama:model:tinyllama", "ollama:model:standard"],
            "default": ["ollama:model:default"],
        }

        # Memory operation restrictions
        self.memory_restrictions = {
            "unload": ["ollama:memory:unload", "ollama:admin"],
            "unload_all": ["ollama:memory:unload_all", "ollama:admin"],
            "status": ["ollama:memory:status", "ollama:admin"],
        }

    def validate_ollama_operation(
        self,
        operation: OllamaOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate if user has permission to perform Ollama operation.

        Args:
            operation: Ollama operation type
            user_roles: List of user roles
            operation_params: Operation parameters for additional validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating Ollama operation: {operation.value}")

            # Check basic operation permissions
            required_permissions = self.ollama_permissions.get(operation, [])
            if not required_permissions:
                return False, f"Unknown Ollama operation: {operation.value}"

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
            self.audit_ollama_operation(
                operation, user_roles, operation_params, "validated"
            )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating Ollama operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, error_msg

    def check_ollama_permissions(
        self, user_roles: List[str], required_permissions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if user has required Ollama permissions.

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
            self.logger.error(f"Error checking Ollama permissions: {str(e)}")
            return False, required_permissions

    def audit_ollama_operation(
        self,
        operation: OllamaOperation,
        user_roles: List[str],
        operation_params: Optional[Dict[str, Any]] = None,
        status: str = "executed",
    ) -> None:
        """
        Audit Ollama operation for security monitoring.

        Args:
            operation: Ollama operation type
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
            self.logger.info(f"Ollama operation audited: {audit_data}")

            # Store audit data (could be extended to write to database)
            self._store_audit_data(audit_data)

        except CustomError as e:
            self.logger.error(f"Error auditing Ollama operation: {str(e)}")

    def get_ollama_roles(self) -> Dict[str, List[str]]:
        """
        Get Ollama-related roles and their permissions.

        Returns:
            Dictionary mapping roles to their Ollama permissions
        """
        try:
            ollama_roles = {}

            # Get all roles from configuration
            all_roles = self.roles_config.get_all_roles()

            for role_name, role_config in all_roles.items():
                role_permissions = role_config.get("permissions", [])
                ollama_permissions = [
                    perm for perm in role_permissions if perm.startswith("ollama:")
                ]

                if ollama_permissions:
                    ollama_roles[role_name] = ollama_permissions

            return ollama_roles

        except CustomError as e:
            self.logger.error(f"Error getting Ollama roles: {str(e)}")
            return {}

    def validate_ollama_api_access(
        self, api_url: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Validate user access to Ollama API.

        Args:
            api_url: Ollama API URL
            user_roles: List of user roles

        Returns:
            Tuple of (has_access, error_message)
        """
        try:
            # Extract API hostname
            api_host = self._extract_api_host(api_url)

            # Check API-specific permissions
            required_permissions = self.api_permissions.get(
                api_host, self.api_permissions["default"]
            )

            has_permission, missing_permissions = self.check_ollama_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to API {api_host}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except ValidationError as e:
            error_msg = f"Error validating API access: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_ollama_model_permissions(
        self,
        model_name: str,
        operation: OllamaOperation,
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Check permissions for specific Ollama model operation.

        Args:
            model_name: Ollama model name
            operation: Ollama operation
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass model-specific checks)
            if self._check_user_permissions(user_roles, ["ollama:admin"]):
                return True, ""

            # Check model access permissions
            model_base = self._extract_model_base_name(model_name)
            model_permissions = self.model_permissions.get(
                model_base, self.model_permissions["default"]
            )

            has_permission, missing_permissions = self.check_ollama_permissions(
                user_roles, model_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to model {model_name}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking model permissions: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def manage_ollama_certificates(
        self, operation: str = "setup", config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Manage Ollama SSL/TLS certificates.

        Args:
            operation: Certificate operation (setup, verify, remove)
            config: Certificate configuration

        Returns:
            Tuple of (success, message)
        """
        try:
            if operation == "setup":
                return self._setup_ollama_ssl_certificates(config)
            elif operation == "verify":
                return self._verify_ollama_ssl_certificates(config)
            elif operation == "remove":
                return self._remove_ollama_ssl_certificates(config)
            else:
                return False, f"Unknown certificate operation: {operation}"

        except SSLError as e:
            error_msg = f"Error managing Ollama certificates: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_ollama_ssl(
        self, ssl_config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Setup SSL/TLS configuration for Ollama connections.

        Args:
            ssl_config: SSL configuration parameters

        Returns:
            Tuple of (success, message)
        """
        try:
            # Default SSL configuration
            default_config = {
                "ssl_verify": True,
                "ssl_cert_path": None,
                "ssl_key_path": None,
                "ssl_ca_path": None,
                "ssl_timeout": 30,
            }

            if ssl_config:
                default_config.update(ssl_config)

            # Store SSL configuration in settings
            self.settings_manager.set("ollama.ssl.verify", default_config["ssl_verify"])
            self.settings_manager.set(
                "ollama.ssl.timeout", default_config["ssl_timeout"]
            )

            if default_config["ssl_cert_path"]:
                self.settings_manager.set(
                    "ollama.ssl.cert_path", default_config["ssl_cert_path"]
                )

            if default_config["ssl_key_path"]:
                self.settings_manager.set(
                    "ollama.ssl.key_path", default_config["ssl_key_path"]
                )

            if default_config["ssl_ca_path"]:
                self.settings_manager.set(
                    "ollama.ssl.ca_path", default_config["ssl_ca_path"]
                )

            self.logger.info("SSL configuration completed for Ollama connections")
            return True, "SSL configuration completed successfully"

        except ConfigurationError as e:
            error_msg = f"Error setting up Ollama SSL: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def check_memory_permissions(
        self, memory_operation: str, user_roles: List[str]
    ) -> Tuple[bool, str]:
        """
        Check permissions for memory operations.

        Args:
            memory_operation: Memory operation type
            user_roles: List of user roles

        Returns:
            Tuple of (has_permission, error_message)
        """
        try:
            # Check if user has admin permissions (bypass memory restrictions)
            if self._check_user_permissions(user_roles, ["ollama:admin"]):
                return True, ""

            # Check memory-specific permissions
            required_permissions = self.memory_restrictions.get(memory_operation, [])

            if not required_permissions:
                return False, f"Unknown memory operation: {memory_operation}"

            has_permission, missing_permissions = self.check_ollama_permissions(
                user_roles, required_permissions
            )

            if not has_permission:
                return (
                    False,
                    f"Access denied to memory operation {memory_operation}. "
                    f"Missing permissions: {missing_permissions}",
                )

            return True, ""

        except PermissionError as e:
            error_msg = f"Error checking memory permissions: {str(e)}"
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
        operation: OllamaOperation,
        operation_params: Dict[str, Any],
        user_roles: List[str],
    ) -> Tuple[bool, str]:
        """
        Validate operation-specific parameters.

        Args:
            operation: Ollama operation
            operation_params: Operation parameters
            user_roles: List of user roles

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if operation in [
                OllamaOperation.MODELS_PULL,
                OllamaOperation.MODELS_RUN,
                OllamaOperation.MODELS_REMOVE,
                OllamaOperation.MODELS_INFO,
            ]:
                return self._validate_model_operation(operation_params, user_roles)
            elif operation == OllamaOperation.RUN_INFERENCE:
                return self._validate_inference_operation(operation_params, user_roles)
            elif operation in [
                OllamaOperation.MEMORY_UNLOAD,
                OllamaOperation.MEMORY_UNLOAD_ALL,
            ]:
                return self._validate_memory_operation(operation_params, user_roles)

            return True, ""

        except ValidationError as e:
            return False, f"Error validating operation parameters: {str(e)}"

    def _validate_model_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Ollama model operation parameters."""
        try:
            # Check model permissions
            model_name = operation_params.get("model_name") or operation_params.get(
                "model"
            )
            if model_name:
                has_permission, error_msg = self.check_ollama_model_permissions(
                    model_name, OllamaOperation.MODEL_ACCESS, user_roles
                )
                if not has_permission:
                    return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating model operation: {str(e)}"

    def _validate_inference_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Ollama inference operation parameters."""
        try:
            # Check model permissions
            model_name = operation_params.get("model_name") or operation_params.get(
                "model"
            )
            if model_name:
                has_permission, error_msg = self.check_ollama_model_permissions(
                    model_name, OllamaOperation.RUN_INFERENCE, user_roles
                )
                if not has_permission:
                    return False, error_msg

            # Check inference parameters
            max_tokens = operation_params.get("max_tokens", 1000)
            if max_tokens > 10000:
                # Check if user has permission for large token generation
                has_permission = self._check_user_permissions(
                    user_roles, ["ollama:inference:large", "ollama:admin"]
                )
                if not has_permission:
                    return False, "Access denied to generate large token counts"

            return True, ""

        except ValidationError as e:
            return False, f"Error validating inference operation: {str(e)}"

    def _validate_memory_operation(
        self, operation_params: Dict[str, Any], user_roles: List[str]
    ) -> Tuple[bool, str]:
        """Validate Ollama memory operation parameters."""
        try:
            # Check memory operation permissions
            action = operation_params.get("action", "status")
            has_permission, error_msg = self.check_memory_permissions(
                action, user_roles
            )
            if not has_permission:
                return False, error_msg

            return True, ""

        except ValidationError as e:
            return False, f"Error validating memory operation: {str(e)}"

    def _extract_api_host(self, api_url: str) -> str:
        """Extract API hostname from URL."""
        try:
            if "://" in api_url:
                return api_url.split("://")[1].split("/")[0]
            else:
                return api_url.split("/")[0]
        except CustomError:
            return "unknown"

    def _extract_model_base_name(self, model_name: str) -> str:
        """Extract base model name from full model name."""
        try:
            # Remove version tags and extract base name
            base_name = model_name.split(":")[0].lower()

            # Map common model names
            model_mapping = {
                "llama2": "llama2",
                "llama3": "llama3",
                "codellama": "codellama",
                "mistral": "mistral",
                "gemma": "gemma",
                "phi": "phi",
                "tinyllama": "tinyllama",
            }

            for key, value in model_mapping.items():
                if key in base_name:
                    return value

            return "default"
        except CustomError:
            return "default"

    def _setup_ollama_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Setup SSL certificates for Ollama connections."""
        try:
            # This could be extended to integrate with mcp-security-framework
            # For now, just configure basic SSL settings
            ssl_config = config or {}

            # Store SSL configuration
            self.settings_manager.set(
                "ollama.ssl.verify", ssl_config.get("ssl_verify", True)
            )
            self.settings_manager.set(
                "ollama.ssl.timeout", ssl_config.get("ssl_timeout", 30)
            )

            return True, "SSL certificates configured successfully"

        except SSLError as e:
            return False, f"Error setting up SSL certificates: {str(e)}"

    def _verify_ollama_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Verify SSL certificates for Ollama connections."""
        try:
            # Check SSL configuration
            ssl_verify = self.settings_manager.get("ollama.ssl.verify", True)
            ssl_timeout = self.settings_manager.get("ollama.ssl.timeout", 30)

            if not ssl_verify:
                return False, "SSL verification is disabled"

            return (
                True,
                f"SSL certificates are properly configured (timeout: {ssl_timeout}s)",
            )

        except SSLError as e:
            return False, f"Error verifying SSL certificates: {str(e)}"

    def _remove_ollama_ssl_certificates(
        self, config: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Remove SSL certificates configuration for Ollama connections."""
        try:
            # Remove SSL configuration
            ssl_configs = [
                "ollama.ssl.verify",
                "ollama.ssl.cert_path",
                "ollama.ssl.key_path",
                "ollama.ssl.ca_path",
                "ollama.ssl.timeout",
            ]

            for config_key in ssl_configs:
                self.settings_manager.remove(config_key)

            return True, "SSL certificates configuration removed"

        except SSLError as e:
            return False, f"Error removing SSL certificates: {str(e)}"

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
