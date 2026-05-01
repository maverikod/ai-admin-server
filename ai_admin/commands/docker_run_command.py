from ai_admin.core.custom_exceptions import CustomError

"""Docker run command for running containers.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""


import subprocess

from typing import Dict, Any, Optional, List

from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult

from ai_admin.commands.base_unified_command import BaseUnifiedCommand

from ai_admin.security.docker_security_adapter import DockerSecurityAdapter

class DockerRunCommand:
    
    
    """Run Docker container with unified security."""
    
    
    name = "docker_run"
    
    
    def __init__(self):
        """Initialize Docker run command with unified security."""
        super().__init__()
        self.docker_security_adapter = DockerSecurityAdapter()
    
    
    async def execute(
        self,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        network: Optional[str] = None,
        detach: bool = True,
        restart: Optional[str] = None,
        user: Optional[str] = None,
        working_dir: Optional[str] = None,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Docker run command with unified security.
    
            Args:
                image: Docker image to run
                name: Container name
                command: Command to run in container
                ports: Port mapping (host_port: container_port)
                volumes: Volume mapping (host_path: container_path)
                environment: Environment variables
                network: Network to connect to
                detach: Run in background
                restart: Restart policy (no, on-failure, always, unless-stopped)
                user: User to run as
                working_dir: Working directory in container
                user_roles: List of user roles for security validation
    
            Returns:
                Success or error result
            """
        # Validate inputs
        if not image:
            return ErrorResult(message="Image is required", code="VALIDATION_ERROR")
    
        # Use unified security approach
        return await super().execute(
            image=image,
            name=name,
            command=command,
            ports=ports,
            volumes=volumes,
            environment=environment,
            network=network,
            detach=detach,
            restart=restart,
            user=user,
            working_dir=working_dir,
            user_roles=user_roles,
            **kwargs,
        )
    
    
    def _get_default_operation(self) -> str:
        """Get default operation name for Docker run command."""
        return "docker:run"
    
    
    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Docker run command logic."""
        return await self._run_container(**kwargs)
    
    
    async def _run_container(
        self,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        network: Optional[str] = None,
        detach: bool = True,
        restart: Optional[str] = None,
        user: Optional[str] = None,
        working_dir: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run Docker container."""
        try:
            cmd = ["docker", "run"]
    
            # Add options
            if detach:
                cmd.append("-d")
    
            if name:
                cmd.extend(["--name", name])
    
            if network:
                cmd.extend(["--network", network])
    
            if restart:
                cmd.extend(["--restart", restart])
    
            if user:
                cmd.extend(["--user", user])
    
            if working_dir:
                cmd.extend(["-w", working_dir])
    
            # Add port mappings
            if ports:
                for host_port, container_port in ports.items():
                    cmd.extend(["-p", f"{host_port}:{container_port}"])
    
            # Add volume mappings
            if volumes:
                for host_path, container_path in volumes.items():
                    cmd.extend(["-v", f"{host_path}:{container_path}"])
    
            # Add environment variables
            if environment:
                for key, value in environment.items():
                    cmd.extend(["-e", f"{key}={value}"])
    
            # Add image
            cmd.append(image)
    
            # Add command if provided
            if command:
                cmd.append(command)
    
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
            if result.returncode != 0:
                raise CustomError(f"Failed to run Docker container: {result.stderr}")
    
            container_id = result.stdout.strip()
    
            return {
                "message": f"Successfully started container from image '{image}'",
                "container_id": container_id,
                "image": image,
                "name": name,
                "network": network,
                "detach": detach,
                "ports": ports,
                "volumes": volumes,
                "environment": environment,
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }
    
        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Docker run command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Docker run failed: {str(e)}")
    
"""Docker run command implementation."""
