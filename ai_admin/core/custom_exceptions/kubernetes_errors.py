"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional
from .base import AIAdminBaseException
from .ssl_errors import CertificateError
from .network_errors import ConnectionError
from .application_errors import ServiceError

class KubernetesError(AIAdminBaseException):
    """Base Kubernetes related error."""
    pass



class K8sConnectionError(KubernetesError):
    """Kubernetes connection error."""
    pass



class K8sResourceError(KubernetesError):
    """Kubernetes resource error."""
    pass



class K8sDeploymentError(K8sResourceError):
    """Kubernetes deployment error."""
    pass



class K8sPodError(K8sResourceError):
    """Kubernetes pod error."""
    pass



class K8sServiceError(K8sResourceError):
    """Kubernetes service error."""
    pass



class K8sConfigMapError(K8sResourceError):
    """Kubernetes configmap error."""
    pass



class K8sNamespaceError(K8sResourceError):
    """Kubernetes namespace error."""
    pass



class K8sCertificateError(K8sResourceError):
    """Kubernetes certificate error."""
    pass


# Git Related Exceptions

