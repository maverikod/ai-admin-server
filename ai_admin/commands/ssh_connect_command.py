"""SSH connect command for establishing SSH connections.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.core.custom_exceptions import CustomError


class SshConnectCommand(BaseUnifiedCommand):
    """SSH connect command for establishing SSH connections with key authentication."""

    name = "ssh_connect"

    def __init__(self):
        """Initialize SSH connect command."""
        super().__init__()

    async def execute(
        self,
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        key_path: Optional[str] = None,
        command: Optional[str] = None,
        timeout: int = 30,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute SSH connection with key authentication.

        Args:
            host: SSH host to connect to
            port: SSH port (default: 22)
            username: SSH username
            key_path: Path to SSH private key
            command: Command to execute remotely
            timeout: Connection timeout in seconds
            user_roles: List of user roles for security validation

        Returns:
            Success result with connection information
        """
        try:
            # Validate inputs
            if not host:
                return ErrorResult(message="Host is required", code="VALIDATION_ERROR")

            # Use unified security approach
            return await super().execute(
                host=host,
                port=port,
                username=username,
                key_path=key_path,
                command=command,
                timeout=timeout,
                user_roles=user_roles,
                **kwargs,
            )

        except CustomError as e:
            return ErrorResult(message=str(e), code="SSH_CONNECTION_ERROR")

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute SSH connection logic."""
        return await self._ssh_connect(**kwargs)

    async def _ssh_connect(
        self,
        host: str,
        port: int = 22,
        username: Optional[str] = None,
        key_path: Optional[str] = None,
        command: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Establish SSH connection and optionally execute command."""
        try:
            # Build SSH command
            ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null"]
            
            # Add port if not default
            if port != 22:
                ssh_cmd.extend(["-p", str(port)])
            
            # Add key if provided
            if key_path and os.path.exists(key_path):
                ssh_cmd.extend(["-i", key_path])
            
            # Add timeout
            ssh_cmd.extend(["-o", f"ConnectTimeout={timeout}"])
            
            # Add username@host
            if username:
                ssh_cmd.append(f"{username}@{host}")
            else:
                ssh_cmd.append(host)
            
            # Add command if provided
            if command:
                ssh_cmd.append(command)
            
            # Execute SSH command
            result = subprocess.run(
                ssh_cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout + 10
            )
            
            return {
                "message": f"SSH connection to {host}:{port}",
                "host": host,
                "port": port,
                "username": username,
                "key_path": key_path,
                "command": command,
                "timeout": timeout,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "ssh_command": " ".join(ssh_cmd),
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            raise CustomError(f"SSH connection to {host}:{port} timed out after {timeout} seconds")
        except Exception as e:
            raise CustomError(f"SSH connection failed: {str(e)}")

    def _get_default_operation(self) -> str:
        """Get default operation name for SSH connect command."""
        return "ssh:connect"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for SSH connect command parameters."""
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "SSH host to connect to"
                },
                "port": {
                    "type": "integer",
                    "default": 22,
                    "description": "SSH port"
                },
                "username": {
                    "type": "string",
                    "description": "SSH username"
                },
                "key_path": {
                    "type": "string",
                    "description": "Path to SSH private key"
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute remotely"
                },
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Connection timeout in seconds"
                }
            },
            "required": ["host"]
        }
