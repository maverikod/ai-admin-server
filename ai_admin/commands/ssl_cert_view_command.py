from ai_admin.core.custom_exceptions import SSLError
"""SSL certificate viewing command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import subprocess
from typing import Optional, List, Dict, Any
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult, CommandResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand


class SSLCertViewCommand(BaseUnifiedCommand):
    """Command to view SSL certificate information."""

    name = "ssl_cert_view"
    description = "View SSL certificate information and details"

    @property
    def resource_type(self) -> str:
        """Get resource type for this command."""
        return "ssl:certificate"

    async def execute(
        self,
        cert_path: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> CommandResult:
        """
        View SSL certificate information.

        Args:
            cert_path: Path to certificate file
            user_roles: List of user roles for security validation

        Returns:
            CommandResult with certificate information
        """
        try:
            # Extract parameters from kwargs
            cert_path = kwargs.get("cert_path") or cert_path
            user_roles = kwargs.get("user_roles") or user_roles or []

            if not cert_path:
                return ErrorResult(
                    message="Certificate path is required",
                    code="MISSING_CERT_PATH",
                    details={"cert_path": cert_path}
                )

            if not os.path.exists(cert_path):
                return ErrorResult(
                    message=f"Certificate file not found: {cert_path}",
                    code="CERT_FILE_NOT_FOUND",
                    details={"cert_path": cert_path}
                )

            # View certificate information
            cert_info = await self._view_certificate(cert_path)
            
            return SuccessResult(
                data={
                    "message": "Certificate information retrieved successfully",
                    "certificate_path": cert_path,
                    "certificate_info": cert_info,
                }
            )

        except SSLError as e:
            return ErrorResult(
                message=f"Failed to view certificate: {str(e)}",
                code="CERT_VIEW_ERROR",
                details={"cert_path": cert_path, "exception": str(e)}
            )

    async def _view_certificate(self, cert_path: str) -> Dict[str, Any]:
        """
        View certificate information using OpenSSL.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with certificate information
        """
        try:
            # Get certificate details using OpenSSL
            cmd = ["openssl", "x509", "-in", cert_path, "-text", "-noout"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse certificate information
            cert_text = result.stdout
            
            # Extract basic information
            basic_info = await self._extract_basic_info(cert_path)
            
            return {
                "basic_info": basic_info,
                "full_text": cert_text,
                "parsed": True,
            }

        except subprocess.CalledProcessError as e:
            raise SSLError(f"OpenSSL command failed: {e.stderr}")
        except SSLError as e:
            raise SSLError(f"Certificate viewing failed: {str(e)}")

    async def _extract_basic_info(self, cert_path: str) -> Dict[str, Any]:
        """
        Extract basic certificate information.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with basic certificate information
        """
        try:
            # Get subject
            subject_cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-subject"]
            subject_result = subprocess.run(
                subject_cmd, capture_output=True, text=True, check=True
            )
            subject = subject_result.stdout.strip().replace("subject=", "")

            # Get issuer
            issuer_cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-issuer"]
            issuer_result = subprocess.run(
                issuer_cmd, capture_output=True, text=True, check=True
            )
            issuer = issuer_result.stdout.strip().replace("issuer=", "")

            # Get dates
            dates_cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-dates"]
            dates_result = subprocess.run(
                dates_cmd, capture_output=True, text=True, check=True
            )
            dates_text = dates_result.stdout.strip()
            
            # Parse dates
            dates = {}
            for line in dates_text.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    dates[key.strip()] = value.strip()

            # Get serial number
            serial_cmd = ["openssl", "x509", "-in", cert_path, "-noout", "-serial"]
            serial_result = subprocess.run(
                serial_cmd, capture_output=True, text=True, check=True
            )
            serial = serial_result.stdout.strip().replace("serial=", "")

            return {
                "subject": subject,
                "issuer": issuer,
                "serial_number": serial,
                "dates": dates,
            }

        except SSLError as e:
            return {
                "error": f"Failed to extract basic info: {str(e)}",
                "subject": "Unknown",
                "issuer": "Unknown",
                "serial_number": "Unknown",
                "dates": {},
            }