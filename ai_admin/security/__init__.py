from ai_admin.core.custom_exceptions import SecurityError
"""AI Admin security package.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .base_security_adapter import SecurityAdapter, SecurityError, SecurityOperation
from .command_security_mixin import CommandSecurityMixin
from .roles_manager import RolesManager
from .security_monitor import (
    SecurityMonitor,
    SecurityEvent,
    SecurityAlert,
    SecurityEventType,
    SecuritySeverity,
)
from .security_metrics import (
    SecurityMetrics,
    MetricPoint,
    MetricSummary,
    MetricType,
    MetricCategory,
)
from .unified_security_integration import (
    UnifiedSecurityIntegration,
    get_unified_security,
    initialize_unified_security,
)
from .docker_security_adapter import DockerSecurityAdapter
from .k8s_security_adapter import K8sSecurityAdapter
from .ftp_security_adapter import FtpSecurityAdapter
from .git_security_adapter import GitSecurityAdapter
from .vast_ai_security_adapter import VastAiSecurityAdapter
from .github_security_adapter import GitHubSecurityAdapter
from .system_security_adapter import SystemSecurityAdapter
from .queue_security_adapter import QueueSecurityAdapter
from .ssl_security_adapter import SSLSecurityAdapter
from .vector_store_security_adapter import VectorStoreSecurityAdapter
from .llm_security_adapter import LLMSecurityAdapter
from .test_security_adapter import TestSecurityAdapter
from .kind_security_adapter import KindSecurityAdapter
from .argocd_security_adapter import ArgoCDSecurityAdapter

__all__ = [
    # Base security components
    "SecurityAdapter",
    "SecurityError",
    "SecurityOperation",
    "CommandSecurityMixin",
    "RolesManager",
    "SecurityMonitor",
    "SecurityEvent",
    "SecurityAlert",
    "SecurityEventType",
    "SecuritySeverity",
    "SecurityMetrics",
    "MetricPoint",
    "MetricSummary",
    "MetricType",
    "MetricCategory",
    "UnifiedSecurityIntegration",
    "get_unified_security",
    "initialize_unified_security",
    # Specialized security adapters
    "DockerSecurityAdapter",
    "K8sSecurityAdapter",
    "FtpSecurityAdapter",
    "GitSecurityAdapter",
    "VastAiSecurityAdapter",
    "GitHubSecurityAdapter",
    "SystemSecurityAdapter",
    "QueueSecurityAdapter",
    "SSLSecurityAdapter",
    "VectorStoreSecurityAdapter",
    "LLMSecurityAdapter",
    "TestSecurityAdapter",
    "KindSecurityAdapter",
    "ArgoCDSecurityAdapter",
]
