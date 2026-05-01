from ai_admin.core.custom_exceptions import SSLError
"""SSL CRL (Certificate Revocation List) command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
from typing import Optional, List, Dict
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.ssl_security_adapter import SSLSecurityAdapter, SSLOperation
from mcp_security_framework import CertificateManager
from mcp_security_framework.schemas import CertificateConfig

class SSLCrlCommand(BaseUnifiedCommand):
    """Command to manage Certificate Revocation Lists (CRL)."""

    name = "ssl_crl"

    def _get_default_operation(self) -> str:
        """Get default operation name for SSLCrlCommand."""
        return "sslcrl:execute"

    def __init__(self) -> None:
        """Initialize SSL CRL command with security adapter."""
        super().__init__()
        self.ssl_security_adapter = SSLSecurityAdapter()
        # Initialize CertificateManager for certificate operations
        self.cert_config = CertificateConfig()
        self.cert_manager = CertificateManager(self.cert_config)

    async def execute(
        self,
        action: str = "create",
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
        crl_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        days_valid: int = 30,
        serial_numbers: Optional[List[str]] = None,
        reason: str = "unspecified",
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Manage Certificate Revocation Lists (CRL).

        Args:
            action: Action to perform (create, add, remove, view, verify)
            ca_cert_path: Path to CA certificate (optional, uses config if not provided)
            ca_key_path: Path to CA private key (optional, uses config if not provided)
            crl_path: Path to CRL file
            output_dir: Output directory for CRL files
            days_valid: Number of days CRL is valid
            serial_numbers: List of certificate serial numbers to add/remove
            reason: Reason for revocation (unspecified, keyCompromise, CACompromise, affiliationChanged,
                    superseded, cessationOfOperation, certificateHold)
            user_roles: List of user roles for security validation
        """
        try:
            # Security validation
            user_roles = user_roles or []

            # Validate SSL operation
            operation_params = {
                "action": action,
                "ca_cert_path": ca_cert_path,
                "crl_path": crl_path,
                "serial_numbers": serial_numbers,
                "reason": reason,
            }

            is_valid, error_msg = self.ssl_security_adapter.validate_ssl_operation(
                SSLOperation.REVOKE, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_VALIDATION_FAILED",
                    details={"error": error_msg, "user_roles": user_roles},
                )
            # Get CA paths from config if not provided
            if not ca_cert_path or not ca_key_path:
                config_paths = await self._get_ca_paths_from_config()
                if not ca_cert_path:
                    ca_cert_path = config_paths.get("ca_cert_path")
                if not ca_key_path:
                    ca_key_path = config_paths.get("ca_key_path")

            if action == "create":
                return await self._create_crl(ca_cert_path, ca_key_path, crl_path, output_dir, days_valid)
            elif action == "add":
                return await self._add_to_crl(ca_cert_path, ca_key_path, crl_path, serial_numbers, reason)
            elif action == "remove":
                return await self._remove_from_crl(ca_cert_path, ca_key_path, crl_path, serial_numbers)
            elif action == "view":
                return await self._view_crl(crl_path)
            elif action == "verify":
                return await self._verify_crl(crl_path, ca_cert_path)
            else:
                return ErrorResult(
                    message="Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={
                        "supported_actions": [
                            "create",
                            "add",
                            "remove",
                            "view",
                            "verify",
                        ]
                    },
                )

        except SSLError as e:
            return ErrorResult(
                message="Failed to manage CRL: {str(e)}",
                code="CRL_OPERATION_FAILED",
                details={"exception": str(e)},
            )

    async def _get_ca_paths_from_config(self) -> Dict[str, str]:
        """Get CA certificate and key paths from configuration."""
        try:
            from ai_admin.settings_manager import get_settings_manager
            
            settings_manager = get_settings_manager()
            config = settings_manager.get_config()
            
            # Get CA paths from SSL configuration
            ssl_config = config.get("ssl", {})
            ca_cert_path = ssl_config.get("ca_cert_path")
            ca_key_path = ssl_config.get("ca_key_path")
            
            return {
                "ca_cert_path": ca_cert_path,
                "ca_key_path": ca_key_path
            }
        except SSLError as e:
            raise SSLError(f"Failed to get CA paths from config: {str(e)}")

    async def _create_crl(
        self, 
        ca_cert_path: str, 
        ca_key_path: str, 
        crl_path: Optional[str], 
        output_dir: Optional[str], 
        days_valid: int
    ) -> CommandResult:
        """Create a new Certificate Revocation List."""
        try:
            import subprocess
            
            if not crl_path:
                if not output_dir:
                    output_dir = os.path.join(os.getcwd(), "crl")
                os.makedirs(output_dir, exist_ok=True)
                crl_path = os.path.join(output_dir, "crl.pem")
            
            # Create CRL using OpenSSL
            cmd = [
                "openssl", "ca", "-gencrl",
                "-config", "/etc/ssl/openssl.cnf",  # You may need to adjust this path
                "-cert", ca_cert_path,
                "-keyfile", ca_key_path,
                "-out", crl_path,
                "-crldays", str(days_valid)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return SuccessResult(
                data={
                    "message": "CRL created successfully",
                    "crl_path": crl_path,
                    "days_valid": days_valid,
                    "output": result.stdout
                }
            )
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to create CRL: {e.stderr}",
                code="CRL_CREATION_FAILED",
                details={"error": e.stderr, "crl_path": crl_path}
            )
        except SSLError as e:
            return ErrorResult(
                message=f"CRL creation failed: {str(e)}",
                code="CRL_CREATION_ERROR",
                details={"crl_path": crl_path, "exception": str(e)}
            )

    async def _add_to_crl(
        self, 
        ca_cert_path: str, 
        ca_key_path: str, 
        crl_path: str, 
        serial_numbers: List[str], 
        reason: str
    ) -> CommandResult:
        """Add certificate serial numbers to CRL."""
        try:
            import subprocess
            
            if not serial_numbers:
                return ErrorResult(
                    message="No serial numbers provided",
                    code="NO_SERIAL_NUMBERS",
                    details={"serial_numbers": serial_numbers}
                )
            
            # Add each serial number to CRL
            for serial in serial_numbers:
                cmd = [
                    "openssl", "ca", "-revoke", serial,
                    "-config", "/etc/ssl/openssl.cnf",
                    "-cert", ca_cert_path,
                    "-keyfile", ca_key_path,
                    "-crl_reason", reason
                ]
                
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Regenerate CRL
            return await self._create_crl(ca_cert_path, ca_key_path, crl_path, None, 30)
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to add to CRL: {e.stderr}",
                code="CRL_ADD_FAILED",
                details={"error": e.stderr, "serial_numbers": serial_numbers}
            )
        except SSLError as e:
            return ErrorResult(
                message=f"Failed to add to CRL: {str(e)}",
                code="CRL_ADD_ERROR",
                details={"serial_numbers": serial_numbers, "exception": str(e)}
            )

    async def _remove_from_crl(
        self, 
        ca_cert_path: str, 
        ca_key_path: str, 
        crl_path: str, 
        serial_numbers: List[str]
    ) -> CommandResult:
        """Remove certificate serial numbers from CRL."""
        try:
            # Note: OpenSSL doesn't directly support removing from CRL
            # This would require parsing the CRL and recreating it
            return ErrorResult(
                message="CRL removal not directly supported by OpenSSL",
                code="CRL_REMOVAL_NOT_SUPPORTED",
                details={"serial_numbers": serial_numbers}
            )
            
        except SSLError as e:
            return ErrorResult(
                message=f"Failed to remove from CRL: {str(e)}",
                code="CRL_REMOVAL_ERROR",
                details={"serial_numbers": serial_numbers, "exception": str(e)}
            )

    async def _view_crl(self, crl_path: str) -> CommandResult:
        """View CRL contents."""
        try:
            import subprocess
            
            if not os.path.exists(crl_path):
                return ErrorResult(
                    message="CRL file not found",
                    code="CRL_NOT_FOUND",
                    details={"crl_path": crl_path}
                )
            
            # View CRL using OpenSSL
            cmd = ["openssl", "crl", "-in", crl_path, "-text", "-noout"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return SuccessResult(
                data={
                    "message": "CRL contents retrieved",
                    "crl_path": crl_path,
                    "contents": result.stdout
                }
            )
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to view CRL: {e.stderr}",
                code="CRL_VIEW_FAILED",
                details={"error": e.stderr, "crl_path": crl_path}
            )
        except SSLError as e:
            return ErrorResult(
                message=f"Failed to view CRL: {str(e)}",
                code="CRL_VIEW_ERROR",
                details={"crl_path": crl_path, "exception": str(e)}
            )

    async def _verify_crl(self, crl_path: str, ca_cert_path: str) -> CommandResult:
        """Verify CRL signature."""
        try:
            import subprocess
            
            if not os.path.exists(crl_path):
                return ErrorResult(
                    message="CRL file not found",
                    code="CRL_NOT_FOUND",
                    details={"crl_path": crl_path}
                )
            
            if not os.path.exists(ca_cert_path):
                return ErrorResult(
                    message="CA certificate not found",
                    code="CA_CERT_NOT_FOUND",
                    details={"ca_cert_path": ca_cert_path}
                )
            
            # Verify CRL using OpenSSL
            cmd = ["openssl", "crl", "-in", crl_path, "-CAfile", ca_cert_path, "-noout"]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            return SuccessResult(
                data={
                    "message": "CRL verification successful",
                    "crl_path": crl_path,
                    "ca_cert_path": ca_cert_path,
                    "is_valid": True
                }
            )
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"CRL verification failed: {e.stderr}",
                code="CRL_VERIFICATION_FAILED",
                details={"error": e.stderr, "crl_path": crl_path}
            )
        except SSLError as e:
            return ErrorResult(
                message=f"CRL verification failed: {str(e)}",
                code="CRL_VERIFICATION_ERROR",
                details={"crl_path": crl_path, "exception": str(e)}
            )
