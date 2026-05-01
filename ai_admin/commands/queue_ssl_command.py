from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import SSLError
"""Queue SSL command for managing SSL certificates in the queue.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.queue_security_adapter import QueueSecurityAdapter

class QueueSSLCommand(BaseUnifiedCommand):
    """Command to manage SSL certificates in the queue.

    This command provides SSL certificate management functionality for queued tasks.
    """

    name = "queue_ssl"
    
    def __init__(self):
        """Initialize queue SSL command."""
        super().__init__()
        self.queue_security_adapter = QueueSecurityAdapter()

    async def execute(
        self,
        action: str = "setup",
        operation: str = "setup",
        user_roles: Optional[List[str]] = None,
        ssl_config: Optional[Dict[str, Any]] = None,
        certificate_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute queue SSL command.
        
        Args:
            action: SSL action (setup, create_cert, update_cert, delete_cert, list_certs, validate_cert, test_connection)
            operation: SSL operation (setup, create_cert, update_cert, delete_cert, list_certs, validate_cert, test_connection)
            user_roles: List of user roles for security validation
            ssl_config: SSL configuration
            certificate_data: Certificate data
            
        Returns:
            Success result with SSL operation status
        """
        # Use unified security approach
        return await super().execute(
            action=action,
            operation=operation,
            user_roles=user_roles,
            ssl_config=ssl_config,
            certificate_data=certificate_data,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for queue SSL command."""
        return "queue:ssl"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute queue SSL command logic."""
        action = kwargs.get("action", "setup")
        operation = kwargs.get("operation", action)
        
        if operation == "setup":
            return await self._setup_ssl(**kwargs)
        elif operation == "create_cert":
            return await self._create_certificate(**kwargs)
        elif operation == "update_cert":
            return await self._update_certificate(**kwargs)
        elif operation == "delete_cert":
            return await self._delete_certificate(**kwargs)
        elif operation == "list_certs":
            return await self._list_certificates(**kwargs)
        elif operation == "validate_cert":
            return await self._validate_certificate(**kwargs)
        elif operation == "test_connection":
            return await self._test_connection(**kwargs)
        else:
            raise SSLError(f"Unknown SSL operation: {operation}")

    async def _setup_ssl(
        self,
        ssl_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Setup SSL configuration for queue."""
        try:
            if not ssl_config:
                ssl_config = {
                    "enabled": True,
                    "cert_path": "/etc/ssl/certs/queue.crt",
                    "key_path": "/etc/ssl/private/queue.key",
                    "ca_path": "/etc/ssl/certs/ca.crt",
                }

            # Mock SSL setup
            setup_result = {
                "ssl_enabled": ssl_config.get("enabled", True),
                "cert_path": ssl_config.get("cert_path"),
                "key_path": ssl_config.get("key_path"),
                "ca_path": ssl_config.get("ca_path"),
                "setup_at": "2024-01-01T00:00:00Z",
            }

            return {
                "message": "SSL setup completed for queue",
                "action": "setup",
                "operation": "setup",
                "ssl_config": ssl_config,
                "setup_result": setup_result,
            }

        except SSLError as e:
            raise SSLError(f"SSL setup failed: {str(e)}")

    async def _create_certificate(
        self,
        certificate_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create SSL certificate for queue."""
        try:
            if not certificate_data:
                certificate_data = {
                    "common_name": "queue.local",
                    "validity_days": 365,
                    "key_size": 2048,
                }

            # Mock certificate creation
            cert_result = {
                "certificate_id": "cert_001",
                "common_name": certificate_data.get("common_name"),
                "validity_days": certificate_data.get("validity_days"),
                "key_size": certificate_data.get("key_size"),
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2025-01-01T00:00:00Z",
            }

            return {
                "message": f"SSL certificate created for {certificate_data.get('common_name')}",
                "action": "create_cert",
                "operation": "create_cert",
                "certificate_data": certificate_data,
                "cert_result": cert_result,
            }

        except SSLError as e:
            raise SSLError(f"Certificate creation failed: {str(e)}")

    async def _update_certificate(
        self,
        certificate_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Update SSL certificate for queue."""
        try:
            if not certificate_data:
                raise SSLError("Certificate data is required for update operation")

            # Mock certificate update
            update_result = {
                "certificate_id": "cert_001",
                "updated_at": "2024-01-01T00:00:00Z",
                "changes": certificate_data,
            }

            return {
                "message": "SSL certificate updated",
                "action": "update_cert",
                "operation": "update_cert",
                "certificate_data": certificate_data,
                "update_result": update_result,
            }

        except SSLError as e:
            raise SSLError(f"Certificate update failed: {str(e)}")

    async def _delete_certificate(
        self,
        certificate_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Delete SSL certificate from queue."""
        try:
            if not certificate_id:
                certificate_id = "cert_001"

            # Mock certificate deletion
            delete_result = {
                "certificate_id": certificate_id,
                "deleted_at": "2024-01-01T00:00:00Z",
            }

            return {
                "message": f"SSL certificate '{certificate_id}' deleted",
                "action": "delete_cert",
                "operation": "delete_cert",
                "certificate_id": certificate_id,
                "delete_result": delete_result,
            }

        except SSLError as e:
            raise SSLError(f"Certificate deletion failed: {str(e)}")

    async def _list_certificates(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """List SSL certificates for queue."""
        try:
            # Mock certificate list
            certificates = [
                {
                    "certificate_id": "cert_001",
                    "common_name": "queue.local",
                    "created_at": "2024-01-01T00:00:00Z",
                    "expires_at": "2025-01-01T00:00:00Z",
                    "status": "active",
                },
                {
                    "certificate_id": "cert_002",
                    "common_name": "api.queue.local",
                    "created_at": "2024-01-01T00:01:00Z",
                    "expires_at": "2025-01-01T00:01:00Z",
                    "status": "active",
                },
            ]

            return {
                "message": f"Found {len(certificates)} SSL certificates",
                "action": "list_certs",
                "operation": "list_certs",
                "certificates": certificates,
                "count": len(certificates),
            }

        except SSLError as e:
            raise SSLError(f"Certificate listing failed: {str(e)}")

    async def _validate_certificate(
        self,
        certificate_id: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Validate SSL certificate for queue."""
        try:
            if not certificate_id:
                certificate_id = "cert_001"

            # Mock certificate validation
            validation_result = {
                "certificate_id": certificate_id,
                "valid": True,
                "expires_at": "2025-01-01T00:00:00Z",
                "days_until_expiry": 365,
                "validated_at": "2024-01-01T00:00:00Z",
            }

            return {
                "message": f"SSL certificate '{certificate_id}' validation completed",
                "action": "validate_cert",
                "operation": "validate_cert",
                "certificate_id": certificate_id,
                "validation_result": validation_result,
            }

        except SSLError as e:
            raise SSLError(f"Certificate validation failed: {str(e)}")

    async def _test_connection(
        self,
        **kwargs,
    ) -> Dict[str, Any]:
        """Test SSL connection for queue."""
        try:
            # Mock connection test
            test_result = {
                "ssl_enabled": True,
                "connection_secure": True,
                "certificate_valid": True,
                "tested_at": "2024-01-01T00:00:00Z",
            }

            return {
                "message": "SSL connection test completed",
                "action": "test_connection",
                "operation": "test_connection",
                "test_result": test_result,
            }

        except SSLError as e:
            raise SSLError(f"Connection test failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for queue SSL command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "SSL action (setup, create_cert, update_cert, delete_cert, list_certs, validate_cert, test_connection)",
                    "default": "setup",
                    "enum": ["setup", "create_cert", "update_cert", "delete_cert", "list_certs", "validate_cert", "test_connection"],
                },
                "operation": {
                    "type": "string",
                    "description": "SSL operation (setup, create_cert, update_cert, delete_cert, list_certs, validate_cert, test_connection)",
                    "default": "setup",
                    "enum": ["setup", "create_cert", "update_cert", "delete_cert", "list_certs", "validate_cert", "test_connection"],
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
                "ssl_config": {
                    "type": "object",
                    "description": "SSL configuration",
                },
                "certificate_data": {
                    "type": "object",
                    "description": "Certificate data",
                },
            },
            "additionalProperties": False,
        }