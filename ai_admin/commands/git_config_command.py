"""Git config command for managing Git configuration."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitConfigCommand(Command):
    """Manage Git configuration.
    
    This command supports:
    - Get configuration values
    - Set configuration values
    - List all configuration
    - Remove configuration
    - Edit configuration file
    - Global vs local configuration
    """
    
    name = "git_config"
    
    async def execute(
        self,
        current_directory: str,
        action: str = "list",
        name: Optional[str] = None,
        value: Optional[str] = None,
        global_config: bool = False,
        local_config: bool = False,
        system_config: bool = False,
        file_config: Optional[str] = None,
        remove: bool = False,
        add: bool = False,
        get_all: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Manage Git configuration.
        
        Args:
            current_directory: Current working directory where to execute git commands
            action: Action to perform (list, get, set, unset, edit)
            name: Configuration name
            value: Configuration value
            global_config: Use global configuration
            local_config: Use local configuration (default)
            system_config: Use system configuration
            file_config: Use specific config file
            remove: Remove configuration
            add: Add configuration
            get_all: Get all values for a name
            repository_path: Path to repository (optional, defaults to current_directory)
        """
        try:
            # Validate current_directory
            if not current_directory:
                return ErrorResult(
                    message="current_directory is required",
                    code="MISSING_CURRENT_DIRECTORY",
                    details={}
                )
            
            if not os.path.exists(current_directory):
                return ErrorResult(
                    message=f"Directory '{current_directory}' does not exist",
                    code="DIRECTORY_NOT_FOUND",
                    details={"current_directory": current_directory}
                )
            
            # Determine repository path
            if not repository_path:
                repository_path = current_directory
            
            # Check if directory is a Git repository (for local config)
            if not local_config and not global_config and not system_config:
                # Default to local config, so check for Git repository
                if not os.path.exists(os.path.join(repository_path, ".git")):
                    return ErrorResult(
                        message=f"'{repository_path}' is not a Git repository for local config",
                        code="NOT_GIT_REPOSITORY",
                        details={"repository_path": repository_path}
                    )
            
            # Build git config command
            cmd = ["git", "config"]
            
            # Add scope flags
            if global_config:
                cmd.append("--global")
            elif system_config:
                cmd.append("--system")
            elif file_config:
                cmd.extend(["--file", file_config])
            # local is default, no flag needed
            
            # Build command based on action
            if action == "list":
                cmd.append("--list")
                
            elif action == "get":
                if not name:
                    return ErrorResult(
                        message="Configuration name is required for get action",
                        code="MISSING_CONFIG_NAME",
                        details={}
                    )
                
                if get_all:
                    cmd.append("--get-all")
                else:
                    cmd.append("--get")
                
                cmd.append(name)
                
            elif action == "set":
                if not name or value is None:
                    return ErrorResult(
                        message="Both name and value are required for set action",
                        code="MISSING_CONFIG_NAME_OR_VALUE",
                        details={}
                    )
                
                if add:
                    cmd.append("--add")
                else:
                    cmd.append("--set")
                
                cmd.extend([name, value])
                
            elif action == "unset":
                if not name:
                    return ErrorResult(
                        message="Configuration name is required for unset action",
                        code="MISSING_CONFIG_NAME",
                        details={}
                    )
                
                if remove:
                    cmd.append("--remove-section")
                else:
                    cmd.append("--unset")
                
                cmd.append(name)
                
            elif action == "edit":
                return ErrorResult(
                    message="Edit action opens an editor and is not supported in automated mode. Use set action instead.",
                    code="EDITOR_NOT_SUPPORTED",
                    details={"suggestion": "Use 'set' action to modify configuration values"}
                )
                
            else:
                return ErrorResult(
                    message=f"Invalid action: {action}",
                    code="INVALID_ACTION",
                    details={"valid_actions": ["list", "get", "set", "unset", "edit"]}
                )
            
            # Execute git config command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                return ErrorResult(
                    message=f"Git config {action} failed: {result.stderr}",
                    code="GIT_CONFIG_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Parse config output
            config_info = await self._parse_config_output(result.stdout, action)
            
            return SuccessResult(data={
                "message": f"Successfully performed {action} action on git config",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "action": action,
                "config_info": config_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git config: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _parse_config_output(self, output: str, action: str) -> Dict[str, Any]:
        """Parse git config output into structured data."""
        if not output.strip():
            return {"message": "No configuration found"}
        
        if action == "list":
            # Parse list output
            config_items = {}
            lines = output.strip().split('\n')
            
            for line in lines:
                if '=' in line:
                    name, value = line.split('=', 1)
                    config_items[name.strip()] = value.strip()
            
            return {
                "config_items": config_items,
                "total_items": len(config_items),
                "message": f"Found {len(config_items)} configuration items"
            }
        
        elif action == "get":
            # Return the value
            return {
                "value": output.strip(),
                "message": "Configuration value retrieved"
            }
        
        elif action == "set":
            return {
                "message": "Configuration value set successfully"
            }
        
        elif action == "unset":
            return {
                "message": "Configuration value unset successfully"
            }
        
        elif action == "edit":
            return {
                "message": "Configuration file opened for editing"
            }
        
        return {
            "raw_output": output.strip(),
            "message": "Configuration operation completed"
        } 