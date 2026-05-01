#!/usr/bin/env python3
"""
Script to add custom exception imports to files that use them.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import re
from pathlib import Path
from typing import Set, List


def find_custom_exceptions_in_file(file_path: Path) -> Set[str]:
    """Find which custom exceptions are used in a file."""
    used_exceptions = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # List of custom exceptions we created
        custom_exceptions = [
            'SSLError', 'CertificateError', 'TLSHandshakeError', 'SSLConfigurationError',
            'MTLSConfigurationError', 'AuthenticationError', 'AuthorizationError', 'TokenError',
            'PermissionError', 'AccessDeniedError', 'ValidationError', 'InvalidInputError',
            'DataValidationError', 'ConfigValidationError', 'ConfigurationError', 'ConfigNotFoundError',
            'ConfigParseError', 'NetworkError', 'ConnectionError', 'TimeoutError', 'ConnectionTimeoutError',
            'FileNotFoundError', 'IOError', 'FilePermissionError', 'DirectoryNotFoundError',
            'DockerError', 'DockerConnectionError', 'DockerImageError', 'DockerContainerError',
            'DockerNetworkError', 'KubernetesError', 'K8sConnectionError', 'K8sResourceError',
            'K8sDeploymentError', 'K8sPodError', 'K8sServiceError', 'K8sConfigMapError',
            'K8sNamespaceError', 'K8sCertificateError', 'GitError', 'GitRepositoryError',
            'GitCommandError', 'GitAuthenticationError', 'QueueError', 'QueueConnectionError',
            'QueueTaskError', 'QueueTimeoutError', 'SecurityError', 'SecurityValidationError',
            'SecurityConfigurationError', 'SecurityAuditError', 'VastAIError', 'VastAIConnectionError',
            'VastAIInstanceError', 'FTPError', 'FTPConnectionError', 'FTPAuthenticationError',
            'FTPTransferError', 'OllamaError', 'OllamaConnectionError', 'OllamaModelError',
            'OllamaInferenceError', 'GitHubError', 'GitHubConnectionError', 'GitHubAuthenticationError',
            'GitHubRepositoryError', 'VectorStoreError', 'VectorStoreConnectionError',
            'VectorStoreConfigurationError', 'LLMError', 'LLMConnectionError', 'LLMInferenceError',
            'LLMConfigurationError', 'SystemError', 'SystemMonitoringError', 'SystemResourceError',
            'CommandError', 'CommandExecutionError', 'CommandTimeoutError', 'CommandValidationError',
            'ApplicationError', 'ServiceError', 'BusinessLogicError', 'IntegrationError',
            'CustomError', 'UnexpectedError'
        ]
        
        for exception in custom_exceptions:
            if exception in content:
                used_exceptions.add(exception)
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return used_exceptions


def add_imports_to_file(file_path: Path, exceptions: Set[str]) -> bool:
    """Add custom exception imports to a file."""
    if not exceptions:
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check if import already exists
        import_line = f"from ai_admin.core.custom_exceptions import {', '.join(sorted(exceptions))}\n"
        
        for line in lines:
            if line.strip().startswith('from ai_admin.core.custom_exceptions import'):
                # Import already exists, check if we need to add more exceptions
                existing_import = line.strip()
                if all(exc in existing_import for exc in exceptions):
                    return False  # All exceptions already imported
                # Need to update import - for now, just skip
                return False
        
        # Find the best place to add import
        import_added = False
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                continue
            elif line.strip() == '' or line.strip().startswith('#'):
                continue
            else:
                # Add import before first non-import line
                lines.insert(i, import_line)
                import_added = True
                break
        
        if not import_added:
            # Add at the beginning if no good place found
            lines.insert(0, import_line)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"Added imports to {file_path}: {', '.join(sorted(exceptions))}")
        return True
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False


def main():
    """Main function."""
    ai_admin_path = Path('ai_admin')
    
    if not ai_admin_path.exists():
        print("ai_admin directory not found")
        return 1
    
    # Find all Python files
    python_files = list(ai_admin_path.rglob('*.py'))
    
    print(f"Found {len(python_files)} Python files")
    
    updated_files = 0
    
    for file_path in python_files:
        # Skip __pycache__ and virtual environments
        if '__pycache__' in str(file_path) or '.venv' in str(file_path):
            continue
        
        # Skip the custom_exceptions.py file itself
        if file_path.name == 'custom_exceptions.py':
            continue
        
        used_exceptions = find_custom_exceptions_in_file(file_path)
        
        if used_exceptions:
            if add_imports_to_file(file_path, used_exceptions):
                updated_files += 1
    
    print(f"\nUpdated {updated_files} files with custom exception imports")
    
    return 0


if __name__ == '__main__':
    exit(main())
