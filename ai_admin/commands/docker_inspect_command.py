"""Docker inspect command for getting detailed container information."""

import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class DockerInspectCommand(Command):
    """Get detailed information about Docker containers, images, or networks.
    
    This command provides detailed information about Docker objects including
    configuration, state, network settings, and more.
    """
    
    name = "docker_inspect"
    
    async def execute(
        self,
        name: str,
        type_filter: Optional[str] = None,
        format_output: Optional[str] = None,
        size: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker inspect command.
        
        Args:
            name: Name or ID of the Docker object (container, image, network, etc.)
            type_filter: Type of object to inspect (container, image, network, volume, etc.)
            format_output: Format output using a template
            size: Display total file sizes for images
            
        Returns:
            Success result with inspection information
        """
        try:
            # Validate inputs
            if not name:
                raise ValidationError("Name or ID is required")
            
            return await self._inspect_object(name, type_filter, format_output, size)
            
        except Exception as e:
            return ErrorResult(
                message=f"Docker inspect command failed: {str(e)}",
                code="DOCKER_INSPECT_ERROR",
                details={"error": str(e), "name": name}
            )
    
    async def _inspect_object(
        self,
        name: str,
        type_filter: Optional[str],
        format_output: Optional[str],
        size: bool
    ) -> SuccessResult:
        """Inspect Docker object."""
        try:
            # Build docker inspect command
            cmd = ["docker", "inspect"]
            
            # Add options
            if type_filter:
                cmd.extend(["--type", type_filter])
            
            if size:
                cmd.append("--size")
            
            # Add format if specified
            if format_output:
                cmd.extend(["--format", format_output])
            
            # Add object name
            cmd.append(name)
            
            # Execute command
            start_time = datetime.now()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = datetime.now()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8')
                return ErrorResult(
                    message=f"Failed to inspect '{name}': {error_output}",
                    code="DOCKER_INSPECT_FAILED",
                    details={
                        "name": name,
                        "stderr": error_output,
                        "command": " ".join(cmd),
                        "exit_code": process.returncode
                    }
                )
            
            # Parse output
            output = stdout.decode('utf-8').strip()
            
            if format_output:
                # Return formatted output as-is
                return SuccessResult(data={
                    "message": f"Successfully inspected '{name}'",
                    "name": name,
                    "format": "custom",
                    "output": output,
                    "command": " ".join(cmd),
                    "execution_time": (end_time - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Parse JSON output
                try:
                    if output.startswith('['):
                        # Multiple objects
                        objects = json.loads(output)
                    else:
                        # Single object
                        objects = [json.loads(output)]
                    
                    return SuccessResult(data={
                        "message": f"Successfully inspected '{name}'",
                        "name": name,
                        "format": "json",
                        "objects": objects,
                        "count": len(objects),
                        "command": " ".join(cmd),
                        "execution_time": (end_time - start_time).total_seconds(),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except json.JSONDecodeError as e:
                    return ErrorResult(
                        message=f"Failed to parse JSON output: {str(e)}",
                        code="JSON_PARSE_ERROR",
                        details={
                            "name": name,
                            "output": output,
                            "error": str(e)
                        }
                    )
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to inspect object: {str(e)}",
                code="DOCKER_INSPECT_FAILED",
                details={"error": str(e), "name": name}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name or ID of the Docker object"
                },
                "type_filter": {
                    "type": "string",
                    "enum": ["container", "image", "network", "volume", "plugin", "secret", "config"],
                    "description": "Type of object to inspect"
                },
                "format_output": {
                    "type": "string",
                    "description": "Format output using a template"
                },
                "size": {
                    "type": "boolean",
                    "description": "Display total file sizes for images",
                    "default": False
                }
            },
            "required": ["name"],
            "additionalProperties": False
        } 