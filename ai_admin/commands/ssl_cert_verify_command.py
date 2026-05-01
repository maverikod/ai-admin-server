from ai_admin.core.custom_exceptions import CertificateError, SSLError
"""SSL certificate verification command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import os

import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand

# from ai_admin.utils.certificate_utils import CertificateUtils  # TODO: Use when implementing certificate utilities
from ai_admin.utils.certificate_exceptions import (
    CertificateError,
)
from ai_admin.security.ssl_security_adapter import SSLSecurityAdapter, SSLOperation
from mcp_security_framework import CertificateManager
from mcp_security_framework.schemas import CertificateConfig

class SSLCertVerifyCommand(BaseUnifiedCommand):
    """Command to verify SSL certificates."""

    name = "ssl_cert_verify"

    def _get_default_operation(self) -> str:
        """Get default operation name for SSLCertVerifyCommand."""
        return "sslcertverify:execute"

    def __init__(self) -> None:
        """Initialize SSL certificate verify command with security adapter."""
        super().__init__()
        self.ssl_security_adapter = SSLSecurityAdapter()
        # Initialize CertificateManager for certificate operations
        self.cert_config = CertificateConfig()
        self.cert_manager = CertificateManager(self.cert_config)

    async def execute(
        self,
        cert_path: str,
        ca_cert_path: Optional[str] = None,
        ca_key_path: Optional[str] = None,
        verify_chain: bool = True,
        check_expiry: bool = True,
        check_revocation: bool = False,
        crl_path: Optional[str] = None,
        check_roles: bool = True,
        required_roles: Optional[List[str]] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Verify SSL certificate with role-based validation.

        Args:
            cert_path: Path to the certificate to verify
            check_roles: Whether to check certificate roles
            required_roles: List of required roles for validation
            ca_cert_path: Path to CA certificate (optional, uses config if not provided)
            ca_key_path: Path to CA private key (optional, uses config if not provided)
            verify_chain: Verify certificate chain
            check_expiry: Check certificate expiry
            check_revocation: Check certificate revocation
            crl_path: Path to CRL file for revocation checking
            user_roles: List of user roles for security validation
        """
        try:
            # Security validation
            user_roles = user_roles or []

            # Validate SSL operation
            operation_params = {
                "cert_path": cert_path,
                "verify_chain": verify_chain,
                "check_expiry": check_expiry,
                "check_revocation": check_revocation,
                "check_roles": check_roles,
                "required_roles": required_roles,
            }

            is_valid, error_msg = self.ssl_security_adapter.validate_ssl_operation(
                SSLOperation.VERIFY, user_roles, operation_params
            )

            if not is_valid:
                return ErrorResult(
                    message="Security validation failed: {error_msg}",
                    code="SECURITY_VALIDATION_FAILED",
                    details={"error": error_msg, "user_roles": user_roles},
                )

            # Validate SSL access
            has_access, access_error = self.ssl_security_adapter.validate_ssl_access(user_roles, cert_path)

            if not has_access:
                return ErrorResult(
                    message="SSL access denied: {access_error}",
                    code="SSL_ACCESS_DENIED",
                    details={"cert_path": cert_path, "error": access_error},
                )
            if not os.path.exists(cert_path):
                return ErrorResult(
                    message="Certificate file not found: {cert_path}",
                    code="FILE_NOT_FOUND",
                    details={"cert_path": cert_path},
                )

            # Get CA paths from config if not provided
            if not ca_cert_path or not ca_key_path:
                config_paths = await self._get_ca_paths_from_config()
                if not ca_cert_path:
                    ca_cert_path = config_paths.get("ca_cert_path")
                if not ca_key_path:
                    ca_key_path = config_paths.get("ca_key_path")

            verification_results = {}

            # Role-based verification using new utilities
            if check_roles:
                try:
                    roles_result = await self._verify_certificate_roles(cert_path, required_roles)
                    verification_results["roles_verification"] = roles_result
                except CertificateError as e:
                    verification_results["roles_verification"] = {
                        "valid": False,
                        "error": str(e),
                        "message": "Role verification failed",
                    }

            # Basic certificate verification
            basic_result = await self._verify_basic_certificate(cert_path)
            verification_results["basic_verification"] = basic_result

            # Certificate chain verification
            if verify_chain and ca_cert_path:
                chain_result = await self._verify_certificate_chain(cert_path, ca_cert_path)
                verification_results["chain_verification"] = chain_result

            # Expiry check
            if check_expiry:
                expiry_result = await self._check_certificate_expiry(cert_path)
                verification_results["expiry_check"] = expiry_result

            # Revocation check
            if check_revocation and crl_path:
                revocation_result = await self._check_certificate_revocation(cert_path, crl_path)
                verification_results["revocation_check"] = revocation_result

            # Overall verification status
            overall_status = self._determine_overall_status(verification_results)

            return SuccessResult(
                data={
                    "message": "Certificate verification completed",
                    "cert_path": cert_path,
                    "ca_cert_path": ca_cert_path,
                    "overall_status": overall_status,
                    "verification_results": verification_results,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except SSLError as e:
            return ErrorResult(
                message="Failed to verify certificate: {str(e)}",
                code="CERT_VERIFICATION_FAILED",
                details={"exception": str(e)},
            )

    async def _get_ca_paths_from_config(self) -> Dict[str, str]:
        """Get CA certificate and key paths from configuration."""
        try:
            from ai_admin.settings_manager import get_settings_manager

            settings_manager = get_settings_manager()
            config = settings_manager.get_all_settings()

            ssl_config = config.get("ssl", {})
            return {
                "ca_cert_path": ssl_config.get("ca_cert_path"),
                "ca_key_path": ssl_config.get("ca_key_path"),
            }
        except SSLError:
            return {}

    async def _verify_basic_certificate(self, cert_path: str) -> Dict[str, Any]:
        """Verify basic certificate format and structure."""
        try:
            # Check certificate format
            result = subprocess.run(
                ["openssl", "x509", "-in", cert_path, "-text", "-noout"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Check certificate dates
            dates_result = subprocess.run(
                ["openssl", "x509", "-in", cert_path, "-dates", "-noout"],
                capture_output=True,
                text=True,
                check=True,
            )

            return {
                "status": "valid",
                "message": "Certificate format is valid",
                "details": result.stdout,
                "dates": dates_result.stdout,
            }

        except subprocess.CalledProcessError as e:
            return {
                "status": "invalid",
                "message": "Certificate format is invalid: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e),
            }

    async def _verify_certificate_chain(self, cert_path: str, ca_cert_path: str) -> Dict[str, Any]:
        """Verify certificate chain against CA certificate."""
        try:
            if not os.path.exists(ca_cert_path):
                return {
                    "status": "error",
                    "message": "CA certificate not found: {ca_cert_path}",
                }

            # Verify certificate against CA
            result = subprocess.run(
                ["openssl", "verify", "-CAfile", ca_cert_path, cert_path],
                capture_output=True,
                text=True,
                check=True,
            )

            if "OK" in result.stdout:
                return {
                    "status": "valid",
                    "message": "Certificate chain is valid",
                    "details": result.stdout,
                }
            else:
                return {
                    "status": "invalid",
                    "message": "Certificate chain verification failed",
                    "details": result.stdout,
                    "error": result.stderr,
                }

        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": "Certificate chain verification error: {e.stderr.decode() if e.stderr else str(e)}",
                "error": str(e),
            }

    async def _check_certificate_expiry(self, cert_path: str) -> Dict[str, Any]:
        """Check certificate expiry date."""
        try:
            # Get certificate end date
            result = subprocess.run(
                ["openssl", "x509", "-in", cert_path, "-enddate", "-noout"],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse the date
            end_date_str = result.stdout.strip().replace("notAfter=", "")

            # Convert to datetime
            from datetime import datetime
            
            # Parse the datetime string
            end_date = datetime.strptime(end_date_str, "%b %d %H:%M:%S %Y %Z")
            
            # Check if certificate is expired
            now = datetime.now()
            is_expired = end_date < now
            
            return SuccessResult(
                data={
                    "message": "Certificate verification completed",
                    "certificate_path": cert_path,
                    "is_valid": not is_expired,
                    "is_expired": is_expired,
                    "expiry_date": end_date.isoformat(),
                    "current_date": now.isoformat(),
                    "days_until_expiry": (end_date - now).days if not is_expired else 0,
                }
            )
            
        except subprocess.CalledProcessError as e:
            return ErrorResult(
                message=f"Failed to verify certificate: {e.stderr}",
                code="CERT_VERIFICATION_FAILED",
                details={"cert_path": cert_path, "error": e.stderr}
            )
        except SSLError as e:
            return ErrorResult(
                message=f"Certificate verification failed: {str(e)}",
                code="CERT_VERIFICATION_ERROR",
                details={"cert_path": cert_path, "exception": str(e)}
            )
