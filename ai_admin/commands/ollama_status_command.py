import subprocess
import json
import psutil
import os
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.ollama_base import ollama_config

class OllamaStatusCommand(Command):
    """Check Ollama status and models in memory."""
    
    name = "ollama_status"
    
    async def execute(self, server: Optional[str] = None, **kwargs):
        """Execute Ollama status check.
        
        Args:
            server: Server name to connect to (optional, uses default if not specified)
            
        Returns:
            Success or error result with status information
        """
        try:
            return await self._get_status(server)
        except Exception as e:
            return ErrorResult(
                message=f"Ollama status check failed: {str(e)}",
                code="OLLAMA_STATUS_ERROR",
                details={"error": str(e), "server": server}
            )
    
    async def _get_status(self, server: Optional[str] = None) -> SuccessResult:
        """Get comprehensive Ollama status."""
        try:
            # Get server configuration
            if server:
                server_config = ollama_config.get_server_config(server)
                if not server_config:
                    return ErrorResult(
                        message=f"Server '{server}' not found in configuration",
                        code="SERVER_NOT_FOUND",
                        details={"available_servers": ollama_config.list_available_servers()}
                    )
                server_url = ollama_config.get_server_url(server)
            else:
                server_url = ollama_config.get_ollama_url()
                server_config = None
            
            # Check if Ollama service is running
            service_status = await self._check_service_status()
            
            # Get models list
            models_status = await self._get_models_status()
            
            # Get memory usage
            memory_status = await self._get_memory_status()
            
            # Get running processes
            processes_status = await self._get_processes_status()
            
            return SuccessResult(data={
                "message": "Ollama status retrieved successfully",
                "server": {
                    "name": server or "default",
                    "url": server_url,
                    "config": server_config
                },
                "service": service_status,
                "models": models_status,
                "memory": memory_status,
                "processes": processes_status,
                "config": {
                    "models_cache_path": ollama_config.get_models_cache_path(),
                    "host": ollama_config.get_ollama_host(),
                    "port": ollama_config.get_ollama_port(),
                    "timeout": ollama_config.get_ollama_timeout()
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Failed to get Ollama status: {str(e)}",
                code="STATUS_CHECK_FAILED",
                details={"error": str(e)}
            )
    
    async def _check_service_status(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Check if Ollama service is running via API."""
        try:
            
            # Get server URL
            if server:
                server_url = ollama_config.get_server_url(server)
            else:
                server_url = ollama_config.get_ollama_url()
            
            if not server_url:
                return {
                    "running": False,
                    "pid": None,
                    "status": "no_url"
                }
            
            # Check API endpoint
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{server_url}/api/version", timeout=5) as response:
                        if response.status == 200:
                            version_data = await response.json()
                            return {
                                "running": True,
                                "pid": None,
                                "status": "active",
                                "version": version_data.get("version"),
                                "url": server_url
                            }
                        else:
                            return {
                                "running": False,
                                "pid": None,
                                "status": f"http_{response.status}"
                            }
                except Exception as e:
                    return {
                        "running": False,
                        "pid": None,
                        "status": "connection_error",
                        "error": str(e)
                    }
            
        except Exception as e:
            return {
                "running": False,
                "pid": None,
                "status": "error",
                "error": str(e)
            }
    
    async def _get_models_status(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Get models list and status via API."""
        try:
            import aiohttp
            
            # Get server URL
            if server:
                server_url = ollama_config.get_server_url(server)
            else:
                server_url = ollama_config.get_ollama_url()
            
            if not server_url:
                return {
                    "available": [],
                    "count": 0,
                    "error": "no_url"
                }
            
            # Get models via API
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{server_url}/api/tags", timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            models_data = data.get("models", [])
                            
                            models = []
                            for model in models_data:
                                model_info = {
                                    "name": model.get("name", "unknown"),
                                    "id": model.get("digest", "unknown"),
                                    "size": model.get("size", "unknown"),
                                    "modified": model.get("modified_at", "unknown")
                                }
                                models.append(model_info)
                            
                            return {
                                "available": models,
                                "count": len(models),
                                "raw_output": str(data)
                            }
                        else:
                            return {
                                "available": [],
                                "count": 0,
                                "error": f"http_{response.status}"
                            }
                except Exception as e:
                    return {
                        "available": [],
                        "count": 0,
                        "error": str(e)
                    }
            
        except Exception as e:
            return {
                "available": [],
                "count": 0,
                "error": str(e)
            }
    
    async def _get_memory_status(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Get memory usage information."""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            
            # Get Ollama processes memory usage
            ollama_memory = 0
            ollama_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    if 'ollama' in proc.info['name'].lower():
                        memory_info = proc.memory_info()
                        ollama_memory += memory_info.rss
                        ollama_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "memory_mb": round(memory_info.rss / 1024 / 1024, 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "system_total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "system_used_gb": round(memory.used / 1024 / 1024 / 1024, 2),
                "system_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "system_percent": memory.percent,
                "ollama_total_mb": round(ollama_memory / 1024 / 1024, 2),
                "ollama_processes": ollama_processes,
                "ollama_process_count": len(ollama_processes)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "ollama_processes": [],
                "ollama_process_count": 0
            }
    
    async def _get_processes_status(self, server: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed Ollama processes information."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
                try:
                    if 'ollama' in proc.info['name'].lower():
                        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                        memory_mb = round(proc.info['memory_info'].rss / 1024 / 1024, 2)
                        
                        process_info = {
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cmdline": cmdline,
                            "memory_mb": memory_mb,
                            "cpu_percent": round(proc.info['cpu_percent'], 2) if proc.info['cpu_percent'] else 0
                        }
                        
                        # Determine process type
                        if 'serve' in cmdline:
                            process_info["type"] = "server"
                        elif 'runner' in cmdline:
                            process_info["type"] = "model_runner"
                        else:
                            process_info["type"] = "other"
                        
                        processes.append(process_info)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "processes": processes,
                "count": len(processes),
                "server_processes": len([p for p in processes if p["type"] == "server"]),
                "runner_processes": len([p for p in processes if p["type"] == "model_runner"])
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "processes": [],
                "count": 0
            }
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get command schema."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        } 