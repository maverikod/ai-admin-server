"""AI Admin - Enhanced MCP Server for managing Docker, Vast.ai, FTP, and Kubernetes resources."""

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import CommandResult, SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import (
    MicroserviceError,
    ValidationError,
    ConfigurationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    TimeoutError,
    InternalError,
    CommandError,
    InvalidParamsError,
    MethodNotFoundError
)

# Import AI Admin specific classes
from ai_admin.commands.base import AIAdminCommand
from ai_admin.settings_manager import get_settings_manager, AIAdminSettingsManager

__version__ = "2.0.0"

__all__ = [
    # Core classes from mcp_proxy_adapter
    "Command",
    "CommandResult", 
    "SuccessResult",
    "ErrorResult",
    "MicroserviceError",
    "ValidationError",
    "ConfigurationError", 
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "TimeoutError",
    "InternalError",
    "CommandError",
    "InvalidParamsError",
    "MethodNotFoundError",
    # AI Admin specific classes
    "AIAdminCommand",
    "get_settings_manager",
    "AIAdminSettingsManager"
] 