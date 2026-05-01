"""SSH exec command for executing commands on remote hosts.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
import os
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.core.custom_exceptions import CustomError


class SshExecCommand(BaseUnifiedCommand):
    """SSH exec command for executing commands on remote hosts."""

    name = "ssh_exec"

    def __init__(self):
        """Initialize SSH exec command."""
        super().__init__()

    async def execute(
        self,
        host: str,
        command: str,
        port: int = 22,
        username: Optional[str] = None,
        key_path: Optional[str] = None,
        timeout: int = 30,
        use_queue: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute command on remote host via SSH.

        Args:
            host: SSH host to connect to
            command: Command to execute remotely
            port: SSH port (default: 22)
            username: SSH username
            key_path: Path to SSH private key
            timeout: Connection timeout in seconds
            user_roles: List of user roles for security validation

        Returns:
            Success result with command execution information
        """
        try:
            # Validate inputs
            if not host:
                return ErrorResult(message="Host is required", code="VALIDATION_ERROR")
            if not command:
                return ErrorResult(message="Command is required", code="VALIDATION_ERROR")

            # Check if we should use queue for long-running commands
            if use_queue or timeout > 60:  # Use queue for commands longer than 1 minute
                from ai_admin.task_queue.queue_manager import queue_manager
                from ai_admin.task_queue.task_queue import TaskType, Task
                
                # Add task to queue
                task_id = await queue_manager.add_task(Task(
                    task_type=TaskType.SSH_EXEC,
                    params={
                        'host': host,
                        'command': command,
                        'port': port,
                        'username': username,
                        'key_path': key_path,
                        'timeout': timeout,
                        'user_roles': user_roles,
                        **kwargs
                    }
                ))
                
                return SuccessResult(
                    data={
                        "message": f"SSH exec task queued successfully",
                        "task_id": task_id,
                        "use_queue": True,
                        "status": "queued",
                        "command": self.name,
                    }
                )

            # Use unified security approach for direct execution
            return await super().execute(
                host=host,
                command=command,
                port=port,
                username=username,
                key_path=key_path,
                timeout=timeout,
                user_roles=user_roles,
                **kwargs,
            )

        except CustomError as e:
            return ErrorResult(message=str(e), code="SSH_EXEC_ERROR")

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute SSH command logic."""
        return await self._ssh_exec(**kwargs)

    async def _ssh_exec(
        self,
        host: str,
        command: str,
        port: int = 22,
        username: Optional[str] = None,
        key_path: Optional[str] = None,
        timeout: int = 30,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute command on remote host via SSH."""
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
            
            # Add command
            ssh_cmd.append(command)
            
            # Execute SSH command
            result = subprocess.run(
                ssh_cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout + 10
            )
            
            return {
                "message": f"SSH command executed on {host}:{port}",
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
            raise CustomError(f"SSH command on {host}:{port} timed out after {timeout} seconds")
        except Exception as e:
            raise CustomError(f"SSH command execution failed: {str(e)}")

    def _get_default_operation(self) -> str:
        """Get default operation name for SSH exec command."""
        return "ssh:exec"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for SSH exec command parameters."""
        return {
            "type": "object",
            "properties": {
                "host": {
                    "type": "string",
                    "description": "SSH host to connect to"
                },
                "command": {
                    "type": "string",
                    "description": "Command to execute remotely"
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
                "timeout": {
                    "type": "integer",
                    "default": 30,
                    "description": "Connection timeout in seconds"
                },
                "use_queue": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use queue for long-running commands"
                }
            },
            "required": ["host", "command"]
        }
