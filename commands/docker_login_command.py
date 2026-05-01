from mcp_proxy_adapter.commands.result import SuccessResult
from ai_admin.core.custom_exceptions import AuthenticationError
"""Docker login command for registry authentication.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerLoginCommand(BaseUnifiedCommand):
    """Authenticate with Docker registries including Docker Hub.

    This command allows logging into Docker registries with username/password
    or using access tokens for secure authentication. If no parameters provided,
    reads credentials from configuration file.
    """

    name = "docker_login"

    def __init__(self):
        """Initialize Docker login command."""
        super().__init__()
        self.security_adapter = DockerSecurityAdapter()

    async def execute(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        registry: str = "https://index.docker.io/v1/",
        email: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker login command with unified security.

        Args:
            username: Registry username
            password: Registry password
            token: Access token for authentication
            registry: Registry URL
            email: Email address (for some registries)
            user_roles: List of user roles for security validation

        Returns:
            Success result with login information
        """
        # Use unified security approach
        return await super().execute(
            username=username,
            password=password,
            token=token,
            registry=registry,
            email=email,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Docker login command."""
        return "docker:login"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker login command logic."""
        return await self._login_to_registry(**kwargs)

    async def _login_to_registry(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        registry: str = "https://index.docker.io/v1/",
        email: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Login to Docker registry."""
        try:
            # Build Docker command
            cmd = ["docker", "login"]

            # Add registry
            if registry != "https://index.docker.io/v1/":
                cmd.append(registry)

            # Add username if provided
            if username:
                cmd.extend(["-u", username])

            # Add email if provided
            if email:
                cmd.extend(["-e", email])

            # Add password or token
            if password:
                cmd.extend(["-p", password])
            elif token:
                cmd.extend(["-p", token])

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                raise AuthenticationError(f"Failed to login to Docker registry: {result.stderr}")

            return {
                "message": f"Successfully logged into Docker registry '{registry}'",
                "registry": registry,
                "username": username,
                "email": email,
                "has_token": bool(token),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise AuthenticationError(f"Docker login command timed out: {str(e)}")
        except AuthenticationError as e:
            raise AuthenticationError(f"Docker login failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker login command parameters."""
        return {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "Registry username",
                },
                "password": {
                    "type": "string",
                    "description": "Registry password",
                },
                "token": {
                    "type": "string",
                    "description": "Access token for authentication",
                },
                "registry": {
                    "type": "string",
                    "description": "Registry URL",
                    "default": "https://index.docker.io/v1/",
                },
                "email": {
                    "type": "string",
                    "description": "Email address (for some registries)",
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
