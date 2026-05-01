"""Module models."""

from ai_admin.core.custom_exceptions import ConfigurationError, CustomError, PermissionError, SSLError, SecurityError, ValidationError
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from enum import Enum
import logging
from ai_admin.settings_manager import get_settings_manager
from ai_admin.config.roles_config import RolesConfig

class SecurityOperation(Enum):
    """Base security operation types."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"



class SecurityError(Exception):
    """Base security error exception."""

    def __init__(self, message: str, code: str = "SECURITY_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)



