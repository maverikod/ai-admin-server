from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""FTP test command for testing FTP server connection.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.ftp_security_adapter import FtpSecurityAdapter
from ai_admin.ftp.ftp_client import FTPClient


class FtpTestCommand(BaseUnifiedCommand):
    """Test FTP server connection with SSL/mTLS security."""

    name = "ftp_test"

    def __init__(self):
        """Initialize FTP test command."""
        super().__init__()
        self.security_adapter = FtpSecurityAdapter()

    async def execute(
        self,
        host: str,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute FTP test operation with SSL/mTLS security.

        Args:
            host: FTP server hostname
            port: FTP server port
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode
            user_roles: List of user roles for security validation

        Returns:
            Success result with connection test information
        """
        # Validate inputs
        if not host:
            return ErrorResult(message="Host is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            host=host,
            port=port,
            username=username,
            password=password,
            use_ftps=use_ftps,
            passive_mode=passive_mode,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for FTP test command."""
        return "ftp:test"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute FTP test command logic."""
        return await self._test_connection(**kwargs)

    async def _test_connection(
        self,
        host: str,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Test FTP server connection."""
        try:
            # Direct FTP operation using FTP client
            with FTPClient(
                host=host,
                port=port,
                username=username,
                password=password,
                use_ftps=use_ftps,
                passive_mode=passive_mode,
            ).connection() as ftp_client:
                result = ftp_client.test_connection()

            return {
                "message": f"FTP connection test successful for {host}:{port}",
                "host": host,
                "port": port,
                "use_ftps": use_ftps,
                "passive_mode": passive_mode,
                "status": "completed",
                "result": result,
            }

        except CustomError as e:
            raise CustomError(f"FTP test failed: {str(e)}")
        except Exception as e:
            raise CustomError(f"FTP test failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for FTP test command parameters."""
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "FTP server hostname",
                },
                "port": {
                    "type": "integer",
                    "description": "FTP server port",
                    "default": 21,
                },
                "username": {
                    "type": "string",
                    "description": "FTP username",
                },
                "password": {
                    "type": "string",
                    "description": "FTP password",
                },
                "use_ftps": {
                    "type": "boolean",
                    "description": "Use FTPS (FTP over SSL/TLS)",
                    "default": False,
                },
                "passive_mode": {
                    "type": "boolean",
                    "description": "Use passive mode",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["host"],
            "additionalProperties": False,
        }
