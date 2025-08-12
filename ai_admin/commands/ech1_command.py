#!/usr/bin/env python3
"""
Ech1 command for testing purposes.
"""

from ai_admin.commands.base import Command, SuccessResult, ErrorResult
from typing import Dict, Any


class Ech1Command(Command):
    """Simple ech1 command for testing.

    This command echoes back the input text, useful for testing
    command execution and parameter passing.
    """

    name = "ech1"

    async def execute(
        self,
        message: str = "Hello, World!",
        **kwargs
    ) -> SuccessResult:
        """Execute ech1 command.

        Args:
            message: Message to echo back

        Returns:
            Success result with echoed message
        """
        try:
            return SuccessResult(data={
                "status": "success",
                "message": "Ech1 command executed successfully",
                "echoed_message": message,
                "timestamp": "2025-08-11T18:00:00.000000"
            })

        except Exception as e:
            return ErrorResult(
                message=f"Ech1 command failed: {str(e)}",
                code="ECH1_ERROR",
                details={"error_type": "execution", "error": str(e)}
            )

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for ech1 command parameters."""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back",
                    "default": "Hello, World!",
                    "examples": ["Hello, World!", "Test message", "CUDA test"]
                }
            },
            "additionalProperties": False
        } 