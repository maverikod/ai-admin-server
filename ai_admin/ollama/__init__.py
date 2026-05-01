"""
Ollama module for AI Admin Server

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .ollama_client import OllamaClient, OllamaModel, OllamaResponse, OllamaModelStatus

__all__ = [
    "OllamaClient",
    "OllamaModel", 
    "OllamaResponse",
    "OllamaModelStatus"
]
