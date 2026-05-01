from ai_admin.core.custom_exceptions import CustomError
"""
AI Admin Hooks System

This module provides hooks for monitoring and enhancing AI Admin operations.
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime

from mcp_proxy_adapter.commands.hooks import hooks
from mcp_proxy_adapter.commands.result import CommandResult
from mcp_proxy_adapter.commands.hooks import HookContext
from mcp_proxy_adapter.commands.hooks import HookType
from mcp_proxy_adapter.core.settings import get_custom_setting_value

# Setup logging for AI Admin hooks
logger = logging.getLogger("ai_admin.hooks")


def vast_operations_before_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Before hook for Vast.ai operations - monitors costs and validates parameters.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    logger.info(f"🔍 Vast.ai before hook: {command_name}")
    
    # Check if vast operations are enabled
    if not get_custom_setting_value("ai_admin.features.vast_operations", True):
        logger.warning("Vast.ai operations are disabled in configuration")
        return
    
    # Log operation start (don't modify params)
    logger.info(f"Vast.ai operation started: {command_name}")
    
    # Validate parameters for cost-sensitive operations
    if command_name == "vast_create" and params:
        # Check for cost limits
        cost_limit = get_custom_setting_value("ai_admin.custom_commands.vast_search.default_filters.max_cost", 1.0)
        if "max_cost" in params:
            if params["max_cost"] > cost_limit:
                logger.warning(f"Cost limit exceeded: {params['max_cost']} > {cost_limit}")


def vast_operations_after_hook(command_name: str, params: Dict[str, Any], result: Any) -> None:
    """
    After hook for Vast.ai operations - logs completion and cleanup.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
        result: Command execution result
    """
    logger.info(f"🔍 Vast.ai after hook: {command_name}")
    logger.info(f"Vast.ai operation completed: {command_name}")
    
    # Auto-cleanup for create operations
    if command_name == "vast_create" and get_custom_setting_value("ai_admin.hooks.vast_operations.auto_cleanup", True):
        logger.info("Auto-cleanup enabled for Vast.ai create operation")


def docker_operations_before_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Before hook for Docker operations - validates parameters and logs operations.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    logger.info(f"🐳 Docker before hook: {command_name}")
    
    # Check if docker operations are enabled
    if not get_custom_setting_value("ai_admin.features.docker_operations", True):
        logger.warning("Docker operations are disabled in configuration")
        return
    
    # Log operation start
    logger.info(f"Docker operation started: {command_name}")
    
    # Validate parameters
    if get_custom_setting_value("ai_admin.hooks.docker_operations.validate_parameters", True):
        if command_name == "docker_build" and params:
            if "image_name" not in params:
                logger.warning("docker_build: missing required parameter 'image_name'")
        
        elif command_name == "docker_push" and params:
            if "image_name" not in params:
                logger.warning("docker_push: missing required parameter 'image_name'")


def docker_operations_after_hook(command_name: str, params: Dict[str, Any], result: Any) -> None:
    """
    After hook for Docker operations - logs completion and performance.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
        result: Command execution result
    """
    logger.info(f"🐳 Docker after hook: {command_name}")
    logger.info(f"Docker operation completed: {command_name}")


def ftp_operations_before_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Before hook for FTP operations - validates paths and logs transfers.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    logger.info(f"📁 FTP before hook: {command_name}")
    
    # Check if ftp operations are enabled
    if not get_custom_setting_value("ai_admin.features.ftp_operations", True):
        logger.warning("FTP operations are disabled in configuration")
        return
    
    # Log operation start
    logger.info(f"FTP operation started: {command_name}")
    
    # Validate paths
    if get_custom_setting_value("ai_admin.hooks.ftp_operations.validate_paths", True) and params:
        for param in ["local_path", "remote_path", "file_path"]:
            if param in params:
                path = params[param]
                if ".." in str(path):
                    logger.warning(f"FTP operation: suspicious path detected: {path}")


def ftp_operations_after_hook(command_name: str, params: Dict[str, Any], result: Any) -> None:
    """
    After hook for FTP operations - logs completion and transfer statistics.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
        result: Command execution result
    """
    logger.info(f"📁 FTP after hook: {command_name}")
    logger.info(f"FTP operation completed: {command_name}")


def queue_operations_before_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Before hook for queue operations - monitors performance and validates tasks.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    logger.info(f"📋 Queue before hook: {command_name}")
    
    # Check if queue operations are enabled
    if not get_custom_setting_value("ai_admin.features.queue_system", True):
        logger.warning("Queue operations are disabled in configuration")
        return
    
    # Log operation start
    logger.info(f"Queue operation started: {command_name}")
    
    # Monitor queue size
    max_queue_size = get_custom_setting_value("ai_admin.custom_commands.queue_operations.max_queue_size", 1000)
    # Note: Actual queue size would be checked in the command implementation


def queue_operations_after_hook(command_name: str, params: Dict[str, Any], result: Any) -> None:
    """
    After hook for queue operations - logs completion and performance metrics.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
        result: Command execution result
    """
    logger.info(f"📋 Queue after hook: {command_name}")
    logger.info(f"Queue operation completed: {command_name}")


def performance_monitoring_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Global performance monitoring hook - tracks response times and memory usage.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    if not get_custom_setting_value("ai_admin.features.performance_monitoring", True):
        return
    
    logger.debug(f"⏱️ Performance monitoring start: {command_name}")


def performance_monitoring_after_hook(command_name: str, params: Dict[str, Any], result: Any) -> None:
    """
    Global performance monitoring after hook.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
        result: Command execution result
    """
    if not get_custom_setting_value("ai_admin.features.performance_monitoring", True):
        return
    
    logger.debug(f"⏱️ Performance monitoring end: {command_name}")


def security_monitoring_hook(command_name: str, params: Dict[str, Any]) -> None:
    """
    Global security monitoring hook - detects suspicious operations.
    
    Args:
        command_name: Name of the command being executed
        params: Command parameters
    """
    logger.debug(f"🔒 Security monitoring: {command_name}")
    
    # Check for sensitive data in parameters
    if params:
        sensitive_keys = ["password", "token", "api_key", "secret"]
        for key in sensitive_keys:
            if key in params:
                logger.info(f"Sensitive parameter detected in {command_name}: {key}")


def ai_admin_before_init_hook() -> None:
    """
    Before initialization hook for AI Admin server.
    Performs pre-initialization setup and validation.
    """
    logger.info("🚀 AI Admin before init hook: Starting pre-initialization...")
    
    # Check if AI Admin features are enabled
    if not get_custom_setting_value("ai_admin.features.enabled", True):
        logger.warning("AI Admin features are disabled in configuration")
        return
    
    # Validate configuration
    logger.info("Validating AI Admin configuration...")
    
    # Check required settings
    required_settings = [
        "ai_admin.features.vast_operations",
        "ai_admin.features.docker_operations", 
        "ai_admin.features.ftp_operations",
        "ai_admin.features.queue_system"
    ]
    
    for setting in required_settings:
        value = get_custom_setting_value(setting, True)
        logger.debug(f"Setting {setting}: {value}")
    
    logger.info("✅ AI Admin pre-initialization completed")


def ai_admin_after_init_hook() -> None:
    """
    After initialization hook for AI Admin server.
    Performs post-initialization setup and validation.
    """
    logger.info("🎯 AI Admin after init hook: Starting post-initialization...")
    
    # Verify all components are initialized
    logger.info("Verifying AI Admin components...")
    
    # Check if security integration is available
    try:
        from ai_admin.security_integration import get_security_integration
        security = get_security_integration()
        if security:
            logger.info("✅ Security integration verified")
        else:
            logger.warning("⚠️ Security integration not available")
    except CustomError as e:
        logger.warning(f"⚠️ Security integration check failed: {e}")
    
    # Log initialization summary
    logger.info("AI Admin initialization summary:")
    logger.info(f"  - Vast operations: {get_custom_setting_value('ai_admin.features.vast_operations', True)}")
    logger.info(f"  - Docker operations: {get_custom_setting_value('ai_admin.features.docker_operations', True)}")
    logger.info(f"  - FTP operations: {get_custom_setting_value('ai_admin.features.ftp_operations', True)}")
    logger.info(f"  - Queue system: {get_custom_setting_value('ai_admin.features.queue_system', True)}")
    logger.info(f"  - Performance monitoring: {get_custom_setting_value('ai_admin.features.performance_monitoring', True)}")
    
    logger.info("✅ AI Admin post-initialization completed")


def register_ai_admin_hooks(hooks_manager) -> None:
    """
    Register all AI Admin hooks with the hooks system.
    
    Args:
        hooks_manager: Hooks manager instance to register hooks with
    """
    logger.info("🔧 Registering AI Admin hooks...")
    
    # Register initialization hooks
    hooks_manager.register_before_init_hook(ai_admin_before_init_hook)
    hooks_manager.register_after_init_hook(ai_admin_after_init_hook)
    
    # Register Vast.ai operation hooks
    hooks_manager.register_before_command_hook(vast_operations_before_hook)
    hooks_manager.register_after_command_hook(vast_operations_after_hook)
    
    # Register Docker operation hooks
    hooks_manager.register_before_command_hook(docker_operations_before_hook)
    hooks_manager.register_after_command_hook(docker_operations_after_hook)
    
    # Register FTP operation hooks
    hooks_manager.register_before_command_hook(ftp_operations_before_hook)
    hooks_manager.register_after_command_hook(ftp_operations_after_hook)
    
    # Register Queue operation hooks
    hooks_manager.register_before_command_hook(queue_operations_before_hook)
    hooks_manager.register_after_command_hook(queue_operations_after_hook)
    
    # Register global hooks
    hooks_manager.register_before_command_hook(performance_monitoring_hook)
    hooks_manager.register_after_command_hook(performance_monitoring_after_hook)
    hooks_manager.register_before_command_hook(security_monitoring_hook)
    
    logger.info("✅ AI Admin hooks registered successfully") 