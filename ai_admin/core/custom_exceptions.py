#!/usr/bin/env python3
"""
Custom exception classes for the AI Admin system.

This module consolidates all custom exception types used throughout the system,
replacing generic Exception usage with specific, meaningful exceptions.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from typing import Any, Dict, Optional


class AIAdminBaseException(Exception):
    """Base exception class for all AI Admin exceptions."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


# SSL/TLS Related Exceptions
class SSLError(AIAdminBaseException):
    """Base SSL/TLS related error."""
    pass


class CertificateError(SSLError):
    """Certificate validation or processing error."""
    pass


class TLSHandshakeError(SSLError):
    """TLS handshake failure."""
    pass


class SSLConfigurationError(SSLError):
    """SSL configuration error."""
    pass


class MTLSConfigurationError(SSLError):
    """mTLS configuration error."""
    pass


# Authentication and Authorization Exceptions
class AuthenticationError(AIAdminBaseException):
    """Authentication failure."""
    pass


class AuthorizationError(AIAdminBaseException):
    """Authorization failure."""
    pass


class TokenError(AuthenticationError):
    """Token validation or processing error."""
    pass


class PermissionError(AIAdminBaseException):
    """Permission denied error."""
    pass


class AccessDeniedError(PermissionError):
    """Access denied error."""
    pass


# Validation Exceptions
class ValidationError(AIAdminBaseException):
    """Data validation error."""
    pass


class InvalidInputError(ValidationError):
    """Invalid input data error."""
    pass


class DataValidationError(ValidationError):
    """Data validation error."""
    pass


class ConfigValidationError(ValidationError):
    """Configuration validation error."""
    pass


# Configuration Exceptions
class ConfigurationError(AIAdminBaseException):
    """Configuration error."""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Configuration file not found."""
    pass


class ConfigParseError(ConfigurationError):
    """Configuration parsing error."""
    pass


# Network and Connection Exceptions
class NetworkError(AIAdminBaseException):
    """Network related error."""
    pass


class ConnectionError(NetworkError):
    """Connection error."""
    pass


class TimeoutError(NetworkError):
    """Operation timeout error."""
    pass


class ConnectionTimeoutError(TimeoutError):
    """Connection timeout error."""
    pass


# File and I/O Exceptions
class FileNotFoundError(AIAdminBaseException):
    """File not found error."""
    pass


class IOError(AIAdminBaseException):
    """I/O operation error."""
    pass


class FilePermissionError(IOError):
    """File permission error."""
    pass


class DirectoryNotFoundError(IOError):
    """Directory not found error."""
    pass


# Docker Related Exceptions
class DockerError(AIAdminBaseException):
    """Base Docker related error."""
    pass


class DockerConnectionError(DockerError):
    """Docker connection error."""
    pass


class DockerImageError(DockerError):
    """Docker image related error."""
    pass


class DockerContainerError(DockerError):
    """Docker container related error."""
    pass


class DockerNetworkError(DockerError):
    """Docker network related error."""
    pass


# Kubernetes Related Exceptions
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
class GitError(AIAdminBaseException):
    """Base Git related error."""
    pass


class GitRepositoryError(GitError):
    """Git repository error."""
    pass


class GitCommandError(GitError):
    """Git command execution error."""
    pass


class GitAuthenticationError(GitError):
    """Git authentication error."""
    pass


# Queue Related Exceptions
class QueueError(AIAdminBaseException):
    """Base queue related error."""
    pass


class QueueConnectionError(QueueError):
    """Queue connection error."""
    pass


class QueueTaskError(QueueError):
    """Queue task error."""
    pass


class QueueTimeoutError(QueueError):
    """Queue operation timeout error."""
    pass


# Security Related Exceptions
class SecurityError(AIAdminBaseException):
    """Base security related error."""
    pass


class SecurityValidationError(SecurityError):
    """Security validation error."""
    pass


class SecurityConfigurationError(SecurityError):
    """Security configuration error."""
    pass


class SecurityAuditError(SecurityError):
    """Security audit error."""
    pass


# Vast.ai Related Exceptions
class VastAIError(AIAdminBaseException):
    """Base Vast.ai related error."""
    pass


class VastAIConnectionError(VastAIError):
    """Vast.ai connection error."""
    pass


class VastAIInstanceError(VastAIError):
    """Vast.ai instance error."""
    pass


# FTP Related Exceptions
class FTPError(AIAdminBaseException):
    """Base FTP related error."""
    pass


class FTPConnectionError(FTPError):
    """FTP connection error."""
    pass


class FTPAuthenticationError(FTPError):
    """FTP authentication error."""
    pass


class FTPTransferError(FTPError):
    """FTP transfer error."""
    pass


# Ollama Related Exceptions
class OllamaError(AIAdminBaseException):
    """Base Ollama related error."""
    pass


class OllamaConnectionError(OllamaError):
    """Ollama connection error."""
    pass


class OllamaModelError(OllamaError):
    """Ollama model error."""
    pass


class OllamaInferenceError(OllamaError):
    """Ollama inference error."""
    pass


# GitHub Related Exceptions
class GitHubError(AIAdminBaseException):
    """Base GitHub related error."""
    pass


class GitHubConnectionError(GitHubError):
    """GitHub connection error."""
    pass


class GitHubAuthenticationError(GitHubError):
    """GitHub authentication error."""
    pass


class GitHubRepositoryError(GitHubError):
    """GitHub repository error."""
    pass


# Vector Store Related Exceptions
class VectorStoreError(AIAdminBaseException):
    """Base vector store related error."""
    pass


class VectorStoreConnectionError(VectorStoreError):
    """Vector store connection error."""
    pass


class VectorStoreConfigurationError(VectorStoreError):
    """Vector store configuration error."""
    pass


# LLM Related Exceptions
class LLMError(AIAdminBaseException):
    """Base LLM related error."""
    pass


class LLMConnectionError(LLMError):
    """LLM connection error."""
    pass


class LLMInferenceError(LLMError):
    """LLM inference error."""
    pass


class LLMConfigurationError(LLMError):
    """LLM configuration error."""
    pass


# System and Monitoring Exceptions
class SystemError(AIAdminBaseException):
    """Base system related error."""
    pass


class SystemMonitoringError(SystemError):
    """System monitoring error."""
    pass


class SystemResourceError(SystemError):
    """System resource error."""
    pass


# Command Related Exceptions
class CommandError(AIAdminBaseException):
    """Base command related error."""
    pass


class CommandExecutionError(CommandError):
    """Command execution error."""
    pass


class CommandTimeoutError(CommandError):
    """Command timeout error."""
    pass


class CommandValidationError(CommandError):
    """Command validation error."""
    pass


# Application Level Exceptions
class ApplicationError(AIAdminBaseException):
    """Base application error."""
    pass


class ServiceError(ApplicationError):
    """Service related error."""
    pass


class BusinessLogicError(ApplicationError):
    """Business logic error."""
    pass


class IntegrationError(ApplicationError):
    """Integration error."""
    pass


# Generic fallback exceptions
class CustomError(AIAdminBaseException):
    """Custom error for specific use cases."""
    pass


class UnexpectedError(AIAdminBaseException):
    """Unexpected error that doesn't fit other categories."""
    pass
