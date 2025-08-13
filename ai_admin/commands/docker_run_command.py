"""Docker run command for running containers."""

import subprocess
import json
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError

class DockerRunCommand(Command):
    """Run Docker container."""
    
    name = "docker_run"
    
    async def execute(self, 
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
                     **kwargs):
        """Execute Docker run command.
        
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
            
        Returns:
            Success or error result
        """
        try:
            # Validate inputs
            if not image:
                raise ValidationError("Image is required")
            
            return await self._run_container(
                image, name, command, ports, volumes, environment,
                network, detach, restart, user, working_dir
            )
        except Exception as e:
            return ErrorResult(
                message=f"Docker run command failed: {str(e)}",
                code="DOCKER_RUN_ERROR",
                details={"error": str(e), "image": image}
            )
    
    async def _run_container(self, image: str, name: Optional[str], command: Optional[str],
                           ports: Optional[Dict[str, str]], volumes: Optional[Dict[str, str]],
                           environment: Optional[Dict[str, str]], network: Optional[str],
                           detach: bool, restart: Optional[str], user: Optional[str],
                           working_dir: Optional[str]) -> SuccessResult:
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
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Failed to run Docker container: {result.stderr}",
                    code="DOCKER_RUN_FAILED",
                    details={"image": image, "stderr": result.stderr, "command": " ".join(cmd)}
                )
            
            container_id = result.stdout.strip()
            
            return SuccessResult(data={
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
                "command": " ".join(cmd)
            })
            
        except subprocess.TimeoutExpired:
            return ErrorResult(
                message="Docker run command timed out",
                code="DOCKER_RUN_TIMEOUT",
                details={"image": image}
            ) 