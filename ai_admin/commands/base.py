"""Base command class for AI Admin Server."""

from typing import Any, Dict
from abc import ABC, abstractmethod
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class AIAdminCommand(Command):
    """Base class for AI Admin server commands.

    This class provides a foundation for creating custom commands
    that can be automatically discovered by the server.
    """

    # Override this in subclasses
    name: str = "ai_admin_command"

    @abstractmethod
    async def execute(self, **kwargs) -> SuccessResult:
        """Execute the command.

        Args:
            **kwargs: Command parameters

        Returns:
            Command execution result
        """
        pass

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for command parameters.

        Returns:
            JSON schema for parameters
        """
        return {"type": "object", "properties": {}, "additionalProperties": True}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is AIAdminCommand:
            return

        if not cls.__dict__.get("descr"):
            doc = (cls.__doc__ or "").strip()
            if doc:
                first_line = doc.split("\n", 1)[0].strip()
                if first_line:
                    cls.descr = first_line

        gs = cls.__dict__.get("get_schema")
        if isinstance(gs, classmethod):
            orig_fn = gs.__func__

            def _schema_impl(subcls):
                schema = orig_fn(subcls)
                if (
                    isinstance(schema, dict)
                    and getattr(subcls, "descr", "")
                    and not schema.get("description")
                ):
                    merged = dict(schema)
                    merged["description"] = subcls.descr
                    return merged
                return schema

            cls.get_schema = classmethod(_schema_impl)  # type: ignore[assignment]


# Backward compatibility
EmptyCommand = AIAdminCommand
