"""Ollama base configuration."""

from ai_admin.core.custom_exceptions import ConfigurationError

"""Base Ollama configuration and utilities.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os


from typing import Dict, Any, Optional

import json


class OllamaConfig:
    """Configuration manager for Ollama."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Ollama configuration.

        Args:
            config_path: Path to config file (optional)
        """
        self.config_path = config_path or os.path.expanduser("~/.ollama/config.json")
        self._config = None

    def load_config(self) -> Dict[str]:
        """Load configuration from file."""
        if self._config is not None:
            return self._config

        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    self._config = json.load(f)
            else:
                self._config = self._get_default_config()
        except ConfigurationError as e:
            print(f"Error loading config: {e}")
            self._config = self._get_default_config()

        return self._config

    def _get_default_config(self) -> Dict[str]:
        """Get default configuration."""
        return {
            "host": "localhost",
            "port": 11434,
            "models": [],
            "timeout": 30,
        }

    def save_config(self, config: Dict[str]) -> bool:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            self._config = config
            return True
        except ConfigurationError as e:
            print(f"Error saving config: {e}")
            return False

    def get_host(self) -> str:
        """Get Ollama host."""
        config = self.load_config()
        return config.get("host", "localhost")

    def get_port(self) -> int:
        """Get Ollama port."""
        config = self.load_config()
        return config.get("port", 11434)

    def get_timeout(self) -> int:
        """Get request timeout."""
        config = self.load_config()
        return config.get("timeout", 30)

    def get_models(self) -> list:
        """Get available models."""
        config = self.load_config()
        return config.get("models", [])

    def add_model(self, model_name: str) -> bool:
        """Add model to configuration."""
        config = self.load_config()
        models = config.get("models", [])
        if model_name not in models:
            models.append(model_name)
            config["models"] = models
            return self.save_config(config)
        return True

    def remove_model(self, model_name: str) -> bool:
        """Remove model from configuration."""
        config = self.load_config()
        models = config.get("models", [])
        if model_name in models:
            models.remove(model_name)
            config["models"] = models
            return self.save_config(config)
        return True
