from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Certificate Revocation List (CRL) operations command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import os

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.config.ssl_config import SSLConfig

class CRLOperationsCommand(BaseUnifiedCommand):
    """Command for Certificate Revocation List (CRL) operations."""

    name = "crl_operations"

    def __init__(self):
        """Initialize CRL operations command."""
        super().__init__()
        self.cert_config = SSLConfig()

    async def execute(
        self,
        action: str = "create",
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
        crl_path: Optional[str] = None,
        validity_days: int = 30,
        revoked_serials: Optional[List[Dict[str, Any]]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute CRL operations with unified security.

        Args:
            action: CRL action (create, update, view, verify)
            ca_cert_path: Path to CA certificate
            ca_key_path: Path to CA private key
            crl_path: Path to CRL file
            validity_days: CRL validity in days
            revoked_serials: List of revoked certificate serials
            user_roles: List of user roles for security validation

        Returns:
            Success result with CRL information
        """
        # Validate inputs
        if not action:
            return ErrorResult(message="Action is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            action=action,
            ca_cert_path=ca_cert_path,
            ca_key_path=ca_key_path,
            crl_path=crl_path,
            validity_days=validity_days,
            revoked_serials=revoked_serials,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for CRL operations command."""
        return "ssl:crl_operations"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute CRL operations logic."""
        return await self._manage_crl(**kwargs)

    async def _manage_crl(
        self,
        action: str = "create",
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
        crl_path: Optional[str] = None,
        validity_days: int = 30,
        revoked_serials: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Manage Certificate Revocation List."""
        try:
            if action == "create":
                if not ca_cert_path or not ca_key_path:
                    raise ValueError("CA certificate and key paths are required for create action")

                if not crl_path:
                    crl_path = os.path.join(os.getcwd(), "certificates", "crl.pem")

                # Create CRL using certificate config
                result = await self.cert_config.create_crl(
                    ca_cert_path=ca_cert_path,
                    ca_key_path=ca_key_path,
                    crl_path=crl_path,
                    validity_days=validity_days,
                    revoked_serials=revoked_serials or []
                )

                return {
                    "message": "CRL created successfully",
                    "crl_path": crl_path,
                    "validity_days": validity_days,
                    "revoked_count": len(revoked_serials or []),
                    "action": action
                }

            elif action == "update":
                if not crl_path:
                    raise ValueError("CRL path is required for update action")

                # Update CRL
                result = await self.cert_config.update_crl(
                    crl_path=crl_path,
                    revoked_serials=revoked_serials or []
                )

                return {
                    "message": "CRL updated successfully",
                    "crl_path": crl_path,
                    "revoked_count": len(revoked_serials or []),
                    "action": action
                }

            elif action == "view":
                if not crl_path:
                    raise ValueError("CRL path is required for view action")

                # View CRL information
                result = await self.cert_config.view_crl(crl_path)

                return {
                    "message": "CRL information retrieved",
                    "crl_path": crl_path,
                    "crl_info": result,
                    "action": action
                }

            elif action == "verify":
                if not crl_path or not ca_cert_path:
                    raise ValueError("CRL and CA certificate paths are required for verify action")

                # Verify CRL
                result = await self.cert_config.verify_crl(crl_path, ca_cert_path)

                return {
                    "message": "CRL verification completed",
                    "crl_path": crl_path,
                    "ca_cert_path": ca_cert_path,
                    "is_valid": result,
                    "action": action
                }

            else:
                raise ValueError(f"Unknown action: {action}")

        except CustomError as e:
            raise CustomError(f"CRL operations failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for CRL operations command parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "CRL action",
                    "enum": ["create", "update", "view", "verify"],
                    "default": "create",
                },
                "ca_cert_path": {
                    "type": "string",
                    "description": "Path to CA certificate",
                },
                "ca_key_path": {
                    "type": "string",
                    "description": "Path to CA private key",
                },
                "crl_path": {
                    "type": "string",
                    "description": "Path to CRL file",
                },
                "validity_days": {
                    "type": "integer",
                    "description": "CRL validity in days",
                    "default": 30,
                },
                "revoked_serials": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of revoked certificate serials",
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
