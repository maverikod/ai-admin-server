"""mTLS Authentication Manager for AI Admin Server.

This module provides comprehensive mTLS authentication management including
client certificate validation, role extraction, permission checking, and
integration with the role-based access control system.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import logging
from ai_admin.core.custom_exceptions import SSLError, CustomError
from ..config.ssl_config import SSLConfig
from ..config.roles_config import RolesConfig
from .ssl_context_manager import SSLContextManager
from .ssl_error_handler import SSLErrorHandler

