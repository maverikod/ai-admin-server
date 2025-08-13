"""Docker exec command for executing commands in containers."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class DockerExecCommand(Command):
    """Execute commands in Docker containers.
    
    This command allows executing arbitrary commands inside running Docker containers.
    """
    
    name = "docker_exec"
    
    async def execute(
        self,
        container: str,
        command: str,
        user: Optional[str] = None,
        workdir: Optional[str] = None,
        env: Optional[List[str]] = None,
        detach: bool = False,
        interactive: bool = False,
        tty: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute command in Docker container.
        
        Args:
            container: Container name or ID
            command: Command to execute
            user: Username or UID to run command as
            workdir: Working directory inside container
            env: Environment variables to set
            detach: Run command in background
            interactive: Keep STDIN open
            tty: Allocate a pseudo-TTY
            **kwargs: Additional arguments
            
        Returns:
            Success result with command output
        """
        try:
            # Validate inputs
            if not container:
                raise ValidationError("Container name or ID is required")
            
            if not command:
                raise ValidationError("Command is required")
            
            return await self._execute_command(
                container, command, user, workdir, env, detach, interactive, tty
            )
            
        except Exception as e:
            return ErrorResult(
                message=f"Docker exec command failed: {str(e)}",
                code="DOCKER_EXEC_ERROR",
                details={"error": str(e), "container": container, "command": command}
            )
    
    async def _execute_command(
        self,
        container: str,
        command: str,
        user: Optional[str],
        workdir: Optional[str],
        env: Optional[List[str]],
        detach: bool,
        interactive: bool,
        tty: bool
    ) -> SuccessResult:
        """Execute command in container."""
        try:
            # Build docker exec command
            cmd = ["docker", "exec"]
            
            # Add options
            if user:
                cmd.extend(["-u", user])
            
            if workdir:
                cmd.extend(["-w", workdir])
            
            if env:
                for env_var in env:
                    cmd.extend(["-e", env_var])
            
            if detach:
                cmd.append("-d")
            
            if interactive:
                cmd.append("-i")
            
            if tty:
                cmd.append("-t")
            
            # Add container and command
            cmd.append(container)
            
            # Split command into parts if it's a string
            if isinstance(command, str):
                cmd.extend(command.split())
            else:
                cmd.extend(command)
            
            # Execute command
            start_time = datetime.now()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = datetime.now()
            
            # Decode output
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""
            
            return SuccessResult(data={
                "message": f"Command executed in container '{container}'",
                "container": container,
                "command": " ".join(cmd),
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": process.returncode,
                "success": process.returncode == 0,
                "execution_time": (end_time - start_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to execute command in container: {str(e)}",
                code="DOCKER_EXEC_FAILED",
                details={"error": str(e), "container": container, "command": command}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "container": {
                    "type": "string",
                    "description": "Container name or ID"
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute"
                },
                "user": {
                    "type": "string",
                    "description": "Username or UID to run command as"
                },
                "workdir": {
                    "type": "string",
                    "description": "Working directory inside container"
                },
                "env": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Environment variables to set"
                },
                "detach": {
                    "type": "boolean",
                    "description": "Run command in background",
                    "default": False
                },
                "interactive": {
                    "type": "boolean",
                    "description": "Keep STDIN open",
                    "default": False
                },
                "tty": {
                    "type": "boolean",
                    "description": "Allocate a pseudo-TTY",
                    "default": False
                }
            },
            "required": ["container", "command"],
            "additionalProperties": False
        } 