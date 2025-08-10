"""Configuration management command."""

import json
import os
from typing import Dict, Any, Optional
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class ConfigCommand(Command):
    """Manage server configuration."""
    
    name = "config"
    
    async def execute(
        self,
        action: str = "get",
        section: Optional[str] = None,
        key: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs
    ) -> SuccessResult:
        """Execute configuration operation.
        
        Args:
            action: Operation to perform (get, set, list)
            section: Configuration section
            key: Configuration key
            value: Configuration value (for set action)
            
        Returns:
            Success or error result
        """
        try:
            config_path = "config/config.json"
            
            if action == "get":
                return await self._get_config(config_path, section, key)
            elif action == "set":
                return await self._set_config(config_path, section, key, value)
            elif action == "list":
                return await self._list_config(config_path)
            else:
                return ErrorResult(
                    message=f"Unknown action: {action}",
                    code="UNKNOWN_ACTION",
                    details={"supported_actions": ["get", "set", "list"]}
                )
                
        except Exception as e:
            return ErrorResult(
                message=f"Configuration operation failed: {str(e)}",
                code="CONFIG_ERROR",
                details={"action": action, "error": str(e)}
            )
    
    async def _get_config(self, config_path: str, section: Optional[str], key: Optional[str]) -> SuccessResult:
        """Get configuration value."""
        try:
            if not os.path.exists(config_path):
                return ErrorResult(
                    message="Configuration file not found",
                    code="CONFIG_FILE_NOT_FOUND",
                    details={"config_path": config_path}
                )
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if section and key:
                # Get specific key in section
                if section not in config:
                    return ErrorResult(
                        message=f"Section '{section}' not found",
                        code="SECTION_NOT_FOUND",
                        details={"available_sections": list(config.keys())}
                    )
                
                section_data = config[section]
                if key not in section_data:
                    return ErrorResult(
                        message=f"Key '{key}' not found in section '{section}'",
                        code="KEY_NOT_FOUND",
                        details={"available_keys": list(section_data.keys())}
                    )
                
                return SuccessResult(data={
                    "action": "get",
                    "section": section,
                    "key": key,
                    "value": section_data[key],
                    "config_path": config_path
                })
                
            elif section:
                # Get entire section
                if section not in config:
                    return ErrorResult(
                        message=f"Section '{section}' not found",
                        code="SECTION_NOT_FOUND",
                        details={"available_sections": list(config.keys())}
                    )
                
                return SuccessResult(data={
                    "action": "get",
                    "section": section,
                    "data": config[section],
                    "config_path": config_path
                })
                
            else:
                # Get entire config
                return SuccessResult(data={
                    "action": "get",
                    "data": config,
                    "config_path": config_path
                })
                
        except json.JSONDecodeError as e:
            return ErrorResult(
                message=f"Invalid JSON in configuration file: {str(e)}",
                code="INVALID_JSON",
                details={"config_path": config_path}
            )
    
    async def _set_config(self, config_path: str, section: str, key: str, value: str) -> SuccessResult:
        """Set configuration value."""
        try:
            if not section or not key or value is None:
                return ErrorResult(
                    message="Section, key, and value are required for set action",
                    code="MISSING_PARAMETERS",
                    details={"section": section, "key": key, "value": value}
                )
            
            # Load existing config
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Create section if it doesn't exist
            if section not in config:
                config[section] = {}
            
            # Set value
            config[section][key] = value
            
            # Save config
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            return SuccessResult(data={
                "action": "set",
                "section": section,
                "key": key,
                "value": value,
                "config_path": config_path,
                "message": f"Configuration updated: {section}.{key} = {value}"
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to set configuration: {str(e)}",
                code="SET_FAILED",
                details={"section": section, "key": key, "value": value}
            )
    
    async def _list_config(self, config_path: str) -> SuccessResult:
        """List configuration structure."""
        try:
            if not os.path.exists(config_path):
                return ErrorResult(
                    message="Configuration file not found",
                    code="CONFIG_FILE_NOT_FOUND",
                    details={"config_path": config_path}
                )
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Build structure overview
            structure = {}
            for section, section_data in config.items():
                if isinstance(section_data, dict):
                    structure[section] = list(section_data.keys())
                else:
                    structure[section] = [type(section_data).__name__]
            
            return SuccessResult(data={
                "action": "list",
                "structure": structure,
                "sections": list(config.keys()),
                "config_path": config_path
            })
            
        except json.JSONDecodeError as e:
            return ErrorResult(
                message=f"Invalid JSON in configuration file: {str(e)}",
                code="INVALID_JSON",
                details={"config_path": config_path}
            )
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Configuration operation",
                    "enum": ["get", "set", "list"],
                    "default": "get"
                },
                "section": {
                    "type": "string",
                    "description": "Configuration section"
                },
                "key": {
                    "type": "string",
                    "description": "Configuration key"
                },
                "value": {
                    "type": "string",
                    "description": "Configuration value (for set action)"
                }
            },
            "required": [],
            "additionalProperties": False
        } 