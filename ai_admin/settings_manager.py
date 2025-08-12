"""
AI Admin Settings Manager

This module provides a settings manager for AI Admin with support for
custom configurations and credential management.
"""

import json
import os
from typing import Dict, Any, Optional
from mcp_proxy_adapter.core.settings import (
    add_custom_settings,
    get_custom_settings,
    get_custom_setting_value,
    set_custom_setting_value
)
from mcp_proxy_adapter.core.logging import get_logger


class AIAdminSettingsManager:
    """
    Settings manager for AI Admin server.
    
    This class provides:
    1. Loading of custom settings from JSON files
    2. Management of credentials and sensitive data
    3. Feature toggles and configuration validation
    4. Integration with the framework's settings system
    """
    
    def __init__(self, config_file: str = "config/config.json", 
                 credentials_file: str = "config/auth.json"):
        """
        Initialize the AI Admin settings manager.
        
        Args:
            config_file: Path to main configuration JSON file
            credentials_file: Path to credentials JSON file
        """
        self.config_file = config_file
        self.credentials_file = credentials_file
        self.logger = get_logger("ai_admin.settings")
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from configuration and credentials files."""
        try:
            # Load main configuration
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_settings = json.load(f)
                
                self.logger.info(f"📁 Loaded configuration from: {self.config_file}")
                
                # Add to framework's settings system
                add_custom_settings(config_settings)
                
            else:
                self.logger.warning(f"⚠️  Configuration file not found: {self.config_file}")
            
            # Load credentials
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    credentials = json.load(f)
                
                self.logger.info(f"🔐 Loaded credentials from: {self.credentials_file}")
                
                # Add credentials to settings system
                add_custom_settings({"credentials": credentials})
                
            else:
                self.logger.warning(f"⚠️  Credentials file not found: {self.credentials_file}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load settings: {e}")
    
    def get_application_name(self) -> str:
        """Get application name."""
        return get_custom_setting_value("ai_admin.application.name", "AI Admin - Enhanced MCP Server")
    
    def get_application_version(self) -> str:
        """Get application version."""
        return get_custom_setting_value("ai_admin.application.version", "2.0.0")
    
    def get_environment(self) -> str:
        """Get application environment."""
        return get_custom_setting_value("ai_admin.application.environment", "production")
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return get_custom_setting_value(f"ai_admin.features.{feature_name}", False)
    
    def get_docker_credentials(self) -> Dict[str, Any]:
        """Get Docker credentials."""
        return get_custom_setting_value("credentials.docker", {})
    
    def get_github_credentials(self) -> Dict[str, Any]:
        """Get GitHub credentials."""
        return get_custom_setting_value("credentials.github", {})
    
    def get_vast_credentials(self) -> Dict[str, Any]:
        """Get Vast.ai credentials."""
        return get_custom_setting_value("credentials.vast", {})
    
    def get_ftp_credentials(self) -> Dict[str, Any]:
        """Get FTP credentials."""
        return get_custom_setting_value("credentials.ftp", {})
    
    def get_ollama_credentials(self) -> Dict[str, Any]:
        """Get Ollama credentials."""
        return get_custom_setting_value("credentials.ollama", {})
    
    def get_command_setting(self, command_name: str, setting_name: str, default: Any = None) -> Any:
        """Get custom command setting."""
        return get_custom_setting_value(f"ai_admin.custom_commands.{command_name}.{setting_name}", default)
    
    def get_hook_setting(self, hook_name: str, setting_name: str, default: Any = None) -> Any:
        """Get hook setting."""
        return get_custom_setting_value(f"ai_admin.hooks.{hook_name}.{setting_name}", default)
    
    def set_custom_setting(self, key: str, value: Any) -> None:
        """Set a custom setting."""
        set_custom_setting_value(key, value)
        self.logger.info(f"🔧 Set custom setting: {key} = {value}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all custom settings."""
        return get_custom_settings()
    
    def reload_settings(self) -> None:
        """Reload settings from files."""
        self.logger.info("🔄 Reloading AI Admin settings...")
        self._load_settings()
        self.logger.info("✅ AI Admin settings reloaded")
    
    def validate_settings(self) -> Dict[str, Any]:
        """
        Validate current settings and return validation results.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate required settings
        required_settings = [
            "ai_admin.application.name",
            "ai_admin.application.version",
            "ai_admin.features.docker_operations"
        ]
        
        for setting in required_settings:
            if get_custom_setting_value(setting) is None:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Missing required setting: {setting}")
        
        # Validate feature dependencies
        if self.is_feature_enabled("docker_operations"):
            docker_creds = self.get_docker_credentials()
            if not docker_creds.get("username") or not docker_creds.get("token"):
                validation_results["warnings"].append(
                    "Docker operations enabled but credentials are missing"
                )
        
        if self.is_feature_enabled("vast_operations"):
            vast_creds = self.get_vast_credentials()
            if not vast_creds.get("api_key"):
                validation_results["warnings"].append(
                    "Vast.ai operations enabled but API key is missing"
                )
        
        if self.is_feature_enabled("ftp_operations"):
            ftp_creds = self.get_ftp_credentials()
            if not ftp_creds.get("host") or not ftp_creds.get("user"):
                validation_results["warnings"].append(
                    "FTP operations enabled but credentials are missing"
                )
        
        return validation_results
    
    def print_settings_summary(self) -> None:
        """Print a summary of current settings."""
        self.logger.info("📊 AI Admin Settings Summary:")
        self.logger.info(f"   Application: {self.get_application_name()} v{self.get_application_version()}")
        self.logger.info(f"   Environment: {self.get_environment()}")
        
        # Features
        features = []
        feature_list = [
            "advanced_hooks", "custom_commands", "data_transformation", 
            "command_interception", "performance_monitoring", "custom_settings_manager",
            "queue_system", "ftp_operations", "docker_operations", "vast_operations",
            "github_operations", "kubernetes_operations", "ollama_operations"
        ]
        
        for feature in feature_list:
            if self.is_feature_enabled(feature):
                features.append(feature)
        
        self.logger.info(f"   Enabled Features: {', '.join(features) if features else 'None'}")
        
        # Security
        auth_enabled = get_custom_setting_value("ai_admin.security.enable_authentication", False)
        rate_limiting = get_custom_setting_value("ai_admin.security.rate_limiting.enabled", False)
        self.logger.info(f"   Security: Auth={auth_enabled}, Rate Limiting={rate_limiting}")
        
        # Monitoring
        metrics_enabled = get_custom_setting_value("ai_admin.monitoring.enable_metrics", False)
        self.logger.info(f"   Monitoring: Metrics={metrics_enabled}")
        
        # Credentials status
        creds_status = []
        if self.get_docker_credentials():
            creds_status.append("Docker")
        if self.get_github_credentials():
            creds_status.append("GitHub")
        if self.get_vast_credentials():
            creds_status.append("Vast.ai")
        if self.get_ftp_credentials():
            creds_status.append("FTP")
        if self.get_ollama_credentials():
            creds_status.append("Ollama")
        
        self.logger.info(f"   Credentials: {', '.join(creds_status) if creds_status else 'None'}")


# Global settings manager instance
_settings_manager = None


def get_settings_manager() -> AIAdminSettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = AIAdminSettingsManager()
    return _settings_manager


# Convenience functions for easy access
def get_app_name() -> str:
    """Get application name."""
    return get_custom_setting_value("ai_admin.application.name", "AI Admin - Enhanced MCP Server")


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return get_custom_setting_value(f"ai_admin.features.{feature_name}", False)


def get_docker_creds() -> Dict[str, Any]:
    """Get Docker credentials."""
    return get_custom_setting_value("credentials.docker", {})


def get_vast_creds() -> Dict[str, Any]:
    """Get Vast.ai credentials."""
    return get_custom_setting_value("credentials.vast", {})


def get_ftp_creds() -> Dict[str, Any]:
    """Get FTP credentials."""
    return get_custom_setting_value("credentials.ftp", {})


def get_command_config(command_name: str, setting_name: str, default: Any = None) -> Any:
    """Get command configuration."""
    return get_custom_setting_value(f"ai_admin.custom_commands.{command_name}.{setting_name}", default) 