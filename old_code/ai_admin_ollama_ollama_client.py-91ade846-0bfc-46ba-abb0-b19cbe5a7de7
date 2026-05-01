"""
Ollama Client with comprehensive model management and inference capabilities

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OllamaModelStatus(Enum):
    """Ollama model status enumeration."""
    PULLING = "pulling"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class OllamaModel:
    """Ollama model information."""
    name: str
    size: int
    digest: str
    modified_at: str
    family: Optional[str] = None
    format: Optional[str] = None
    families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


@dataclass
class OllamaResponse:
    """Ollama API response."""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """Enhanced Ollama client with comprehensive model management and inference capabilities."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
        verify_ssl: bool = True,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server base URL
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            api_key: API key for authentication (if required)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to Ollama server."""
        if self._session is None:
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            headers = {}
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            logger.info(f"Connected to Ollama server at {self.base_url}")

    async def disconnect(self) -> None:
        """Close connection to Ollama server."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("Disconnected from Ollama server")

    @asynccontextmanager
    async def connection(self):
        """Context manager for Ollama connection."""
        await self.connect()
        try:
            yield self
        finally:
            await self.disconnect()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Ollama API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data

        Returns:
            Response data
        """
        if not self._session:
            await self.connect()

        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                async with self._session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            
            elif method.upper() == "POST":
                async with self._session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            
            elif method.upper() == "DELETE":
                async with self._session.delete(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise

    async def _make_streaming_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Make streaming HTTP request to Ollama API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data

        Yields:
            Response data chunks
        """
        if not self._session:
            await self.connect()

        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                async with self._session.post(url, json=data) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                try:
                                    yield json.loads(line.decode('utf-8'))
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            else:
                raise ValueError(f"Unsupported HTTP method for streaming: {method}")
                
        except Exception as e:
            logger.error(f"Streaming request failed: {e}")
            raise

    async def get_version(self) -> Dict[str, Any]:
        """
        Get Ollama server version information.

        Returns:
            Version information dictionary
        """
        try:
            result = await self._make_request("GET", "/api/version")
            logger.info(f"Ollama version: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            raise

    async def list_models(self) -> List[OllamaModel]:
        """
        List all available models.

        Returns:
            List of OllamaModel objects
        """
        try:
            result = await self._make_request("GET", "/api/tags")
            models = []
            
            for model_data in result.get("models", []):
                model = OllamaModel(
                    name=model_data.get("name", ""),
                    size=model_data.get("size", 0),
                    digest=model_data.get("digest", ""),
                    modified_at=model_data.get("modified_at", ""),
                    family=model_data.get("family"),
                    format=model_data.get("format"),
                    families=model_data.get("families"),
                    parameter_size=model_data.get("parameter_size"),
                    quantization_level=model_data.get("quantization_level"),
                )
                models.append(model)
            
            logger.info(f"Found {len(models)} models")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise

    async def pull_model(
        self,
        model_name: str,
        insecure: bool = False,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull/download a model from registry.

        Args:
            model_name: Name of the model to pull
            insecure: Whether to use insecure registry
            stream: Whether to stream progress

        Yields:
            Progress updates during download
        """
        try:
            data = {
                "name": model_name,
                "insecure": insecure,
                "stream": stream
            }
            
            logger.info(f"Pulling model: {model_name}")
            async for progress in self._make_streaming_request("POST", "/api/pull", data):
                yield progress
                
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            raise

    async def push_model(
        self,
        model_name: str,
        insecure: bool = False,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Push a model to registry.

        Args:
            model_name: Name of the model to push
            insecure: Whether to use insecure registry
            stream: Whether to stream progress

        Yields:
            Progress updates during upload
        """
        try:
            data = {
                "name": model_name,
                "insecure": insecure,
                "stream": stream
            }
            
            logger.info(f"Pushing model: {model_name}")
            async for progress in self._make_streaming_request("POST", "/api/push", data):
                yield progress
                
        except Exception as e:
            logger.error(f"Failed to push model {model_name}: {e}")
            raise

    async def remove_model(self, model_name: str) -> Dict[str, Any]:
        """
        Remove a model from local storage.

        Args:
            model_name: Name of the model to remove

        Returns:
            Removal result
        """
        try:
            data = {"name": model_name}
            result = await self._make_request("DELETE", "/api/delete", data)
            logger.info(f"Removed model: {model_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to remove model {model_name}: {e}")
            raise

    async def show_model(self, model_name: str) -> Dict[str, Any]:
        """
        Show model information and parameters.

        Args:
            model_name: Name of the model

        Returns:
            Model information dictionary
        """
        try:
            data = {"name": model_name}
            result = await self._make_request("POST", "/api/show", data)
            logger.info(f"Retrieved model info for: {model_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to show model {model_name}: {e}")
            raise

    async def copy_model(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a model to a new name.

        Args:
            source: Source model name
            destination: Destination model name

        Returns:
            Copy result
        """
        try:
            data = {
                "source": source,
                "destination": destination
            }
            result = await self._make_request("POST", "/api/copy", data)
            logger.info(f"Copied model from {source} to {destination}")
            return result
        except Exception as e:
            logger.error(f"Failed to copy model from {source} to {destination}: {e}")
            raise

    async def generate(
        self,
        model: str,
        prompt: str,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        raw: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text using a model.

        Args:
            model: Model name
            prompt: Input prompt
            stream: Whether to stream response
            format: Response format
            options: Model options (temperature, max_tokens, etc.)
            system: System prompt
            template: Template for formatting
            context: Previous context
            raw: Whether to use raw mode

        Returns:
            Generated response or async generator for streaming
        """
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "raw": raw
            }
            
            if format:
                data["format"] = format
            if options:
                data["options"] = options
            if system:
                data["system"] = system
            if template:
                data["template"] = template
            if context:
                data["context"] = context
            
            logger.info(f"Generating with model: {model}")
            
            result = await self._make_request("POST", "/api/generate", data)
            return result
                
        except Exception as e:
            logger.error(f"Failed to generate with model {model}: {e}")
            raise

    async def generate_stream(
        self,
        model: str,
        prompt: str,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None,
        template: Optional[str] = None,
        context: Optional[List[int]] = None,
        raw: bool = False,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate text using a model with streaming.

        Args:
            model: Model name
            prompt: Input prompt
            format: Response format
            options: Model options
            system: System prompt
            template: Template
            context: Context
            raw: Raw mode

        Yields:
            Response chunks
        """
        try:
            data = {
                "model": model,
                "prompt": prompt,
                "stream": True,
                "raw": raw
            }
            
            if format:
                data["format"] = format
            if options:
                data["options"] = options
            if system:
                data["system"] = system
            if template:
                data["template"] = template
            if context:
                data["context"] = context
            
            logger.info(f"Generating with model: {model} (streaming)")
            
            async for response in self._make_streaming_request("POST", "/api/generate", data):
                yield response
                
        except Exception as e:
            logger.error(f"Failed to generate with model {model}: {e}")
            raise

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Chat with a model using conversation format.

        Args:
            model: Model name
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream response
            format: Response format
            options: Model options

        Returns:
            Chat response or async generator for streaming
        """
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            if format:
                data["format"] = format
            if options:
                data["options"] = options
            
            logger.info(f"Chatting with model: {model}")
            
            result = await self._make_request("POST", "/api/chat", data)
            return result
                
        except Exception as e:
            logger.error(f"Failed to chat with model {model}: {e}")
            raise

    async def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Chat with a model using conversation format with streaming.

        Args:
            model: Model name
            messages: List of message dictionaries with 'role' and 'content'
            format: Response format
            options: Model options

        Yields:
            Response chunks
        """
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": True
            }
            
            if format:
                data["format"] = format
            if options:
                data["options"] = options
            
            logger.info(f"Chatting with model: {model} (streaming)")
            
            async for response in self._make_streaming_request("POST", "/api/chat", data):
                yield response
                
        except Exception as e:
            logger.error(f"Failed to chat with model {model}: {e}")
            raise

    async def create_model(
        self,
        model_name: str,
        modelfile: str,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a model from a Modelfile.

        Args:
            model_name: Name for the new model
            modelfile: Modelfile content
            stream: Whether to stream progress

        Yields:
            Progress updates during creation
        """
        try:
            data = {
                "name": model_name,
                "modelfile": modelfile,
                "stream": stream
            }
            
            logger.info(f"Creating model: {model_name}")
            async for progress in self._make_streaming_request("POST", "/api/create", data):
                yield progress
                
        except Exception as e:
            logger.error(f"Failed to create model {model_name}: {e}")
            raise

    async def get_embeddings(
        self,
        model: str,
        prompt: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get embeddings for a prompt.

        Args:
            model: Model name
            prompt: Input prompt
            options: Model options

        Returns:
            Embeddings response
        """
        try:
            data = {
                "model": model,
                "prompt": prompt
            }
            
            if options:
                data["options"] = options
            
            logger.info(f"Getting embeddings with model: {model}")
            result = await self._make_request("POST", "/api/embeddings", data)
            return result
                
        except Exception as e:
            logger.error(f"Failed to get embeddings with model {model}: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Ollama server.

        Returns:
            Connection test result
        """
        try:
            version_info = await self.get_version()
            models = await self.list_models()
            
            return {
                "status": "connected",
                "base_url": self.base_url,
                "version": version_info,
                "models_count": len(models),
                "available_models": [model.name for model in models]
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "status": "failed",
                "base_url": self.base_url,
                "error": str(e)
            }
