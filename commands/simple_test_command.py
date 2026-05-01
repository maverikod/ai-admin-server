#!/usr/bin/env python3
"""
Simple test command for MCP server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class SimpleTestCommand(Command):
    """Simple test command."""
    
    name = "simple_test"
    descr = "Simple test command"
    category = "test"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"
    version = "1.0.0"
    
    @staticmethod
    def get_schema():
        """Get command schema."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Test message",
                    "default": "Hello World"
                }
            },
            "required": []
        }
    
    async def execute(self, message: str = "Hello World", **kwargs):
        """Execute the test command."""
        try:
            return SuccessResult(
                data={
                    "message": message,
                    "status": "success",
                    "timestamp": "2025-01-27T16:00:00Z"
                },
                message=f"Test command executed successfully: {message}"
            )
        except Exception as e:
            return ErrorResult(
                message=f"Test command failed: {str(e)}",
                error_code="TEST_ERROR"
            )
