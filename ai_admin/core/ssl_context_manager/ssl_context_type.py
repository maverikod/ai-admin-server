"""SSL context type enum."""

from enum import Enum

class SSLContextType(Enum):
    """Types of SSL contexts."""
    HTTPS = "https"
    MTLS = "mtls"
    TOKEN_AUTH = "token_auth"
    MIXED = "mixed"