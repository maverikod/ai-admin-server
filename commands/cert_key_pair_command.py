from ai_admin.core.custom_exceptions import SSLError
"""Certificate key pair generation command.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import os

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.utils.certificate_utils import CertificateUtils

class CertKeyPairCommand(BaseUnifiedCommand):
    """Command for generating certificate-key pairs."""

    name = "cert_key_pair"

    def __init__(self):
        """Initialize certificate key pair command."""
        super().__init__()
        self.cert_utils = CertificateUtils()

    async def execute(
        self,
        cert_type: str = "client",
        common_name: str = "test-client",
        organization: str = "Test Organization",
        country: str = "US",
        state: str = "CA",
        city: str = "San Francisco",
        email: str = "test@example.com",
        validity_days: int = 365,
        key_size: int = 2048,
        output_dir: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute certificate key pair generation with unified security.

        Args:
            cert_type: Type of certificate (client, server, ca)
            common_name: Common name for the certificate
            organization: Organization name
            country: Country code
            state: State or province
            city: City name
            email: Email address
            validity_days: Certificate validity in days
            key_size: Key size in bits
            output_dir: Output directory for files
            user_roles: List of user roles for security validation

        Returns:
            Success result with certificate information
        """
        # Validate inputs
        if not common_name:
            return ErrorResult(message="Common name is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            cert_type=cert_type,
            common_name=common_name,
            organization=organization,
            country=country,
            state=state,
            city=city,
            email=email,
            validity_days=validity_days,
            key_size=key_size,
            output_dir=output_dir,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for certificate key pair command."""
        return "ssl:cert_key_pair"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute certificate key pair generation logic."""
        return await self._generate_cert_key_pair(**kwargs)

    async def _generate_cert_key_pair(
        self,
        cert_type: str = "client",
        common_name: str = "test-client",
        organization: str = "Test Organization",
        country: str = "US",
        state: str = "CA",
        city: str = "San Francisco",
        email: str = "test@example.com",
        validity_days: int = 365,
        key_size: int = 2048,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate certificate key pair."""
        try:
            # Set default output directory
            if not output_dir:
                output_dir = os.path.join(os.getcwd(), "certificates", cert_type)

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Generate certificate and key
            cert_path, key_path = await self.cert_utils.generate_cert_key_pair(
                cert_type=cert_type,
                common_name=common_name,
                organization=organization,
                country=country,
                state=state,
                city=city,
                email=email,
                validity_days=validity_days,
                key_size=key_size,
                output_dir=output_dir,
            )

            return {
                "message": f"Certificate key pair generated for '{common_name}'",
                "cert_type": cert_type,
                "common_name": common_name,
                "cert_path": cert_path,
                "key_path": key_path,
                "output_dir": output_dir,
                "validity_days": validity_days,
                "key_size": key_size,
                "status": "generated"
            }

        except SSLError as e:
            raise SSLError(f"Certificate key pair generation failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for certificate key pair command parameters."""
        return {
            "type": "object",
            "properties": {
                "cert_type": {
                    "type": "string",
                    "description": "Type of certificate",
                    "enum": ["client", "server", "ca"],
                    "default": "client",
                },
                "common_name": {
                    "type": "string",
                    "description": "Common name for the certificate",
                    "default": "test-client",
                },
                "organization": {
                    "type": "string",
                    "description": "Organization name",
                    "default": "Test Organization",
                },
                "country": {
                    "type": "string",
                    "description": "Country code",
                    "default": "US",
                },
                "state": {
                    "type": "string",
                    "description": "State or province",
                    "default": "CA",
                },
                "city": {
                    "type": "string",
                    "description": "City name",
                    "default": "San Francisco",
                },
                "email": {
                    "type": "string",
                    "description": "Email address",
                    "default": "test@example.com",
                },
                "validity_days": {
                    "type": "integer",
                    "description": "Certificate validity in days",
                    "default": 365,
                },
                "key_size": {
                    "type": "integer",
                    "description": "Key size in bits",
                    "default": 2048,
                },
                "output_dir": {
                    "type": "string",
                    "description": "Output directory for files",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["common_name"],
            "additionalProperties": False,
        }
