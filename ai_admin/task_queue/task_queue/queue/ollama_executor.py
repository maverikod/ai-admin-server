"""Module queue."""

from ai_admin.core.custom_exceptions import (
    ConfigurationError,
    CustomError,
    NetworkError,
)
import asyncio
import json
import uuid
import ssl
import socket
import ftplib
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field

class OllamaExecutor:
    """Universal task queue for managing any type of operations."""

    async def _execute_ollama_pull_task(self, task: Task) -> None:
        """Execute Ollama model pull task."""
        import os
        from ai_admin.commands.ollama_base import OllamaConfig

        ollama_config = OllamaConfig()
        params = task.params
        model_name = params.get("model_name", "")
        task.update_progress(5, f"Starting pull of Ollama model: {model_name}")
        env = os.environ.copy()
        env["OLLAMA_MODELS"] = ollama_config.get_models_cache_path()
        cmd = ["ollama", "pull", model_name]
        task.command = " ".join(cmd)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        task.update_progress(15, "Downloading model layers...")
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            task.update_progress(95, "Finalizing model download...")
            output_lines = stdout.decode("utf-8").splitlines()
            model_size = None
            for line in output_lines:
                if "pulled" in line.lower() and "mb" in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if "mb" in part.lower() or "gb" in part.lower():
                            model_size = part
                            break
            result = {
                "status": "success",
                "message": f"Ollama model {model_name} pulled successfully",
                "model_name": model_name,
                "model_size": model_size,
                "output": output_lines,
            }
            task.complete(result)
        else:
            error_msg = stderr.decode("utf-8").strip()
            task.fail(f"Ollama pull failed: {error_msg}")

    async def _execute_ollama_run_task(self, task: Task) -> None:
        """Execute Ollama model inference task."""
        from ai_admin.commands.ollama_base import OllamaConfig

        ollama_config = OllamaConfig()
        params = task.params
        model_name = params.get("model_name", "")
        prompt = params.get("prompt", "")
        max_tokens = params.get("max_tokens", 1000)
        temperature = params.get("temperature", 0.7)
        task.update_progress(10, f"Starting inference with model: {model_name}")
        request_data = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        curl_cmd = [
            "curl",
            "-s",
            "-X",
            "POST",
            f"{ollama_config.get_ollama_url()}/api/generate",
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(request_data),
        ]
        task.command = " ".join(curl_cmd)
        task.update_progress(25, "Sending request to Ollama...")
        process = await asyncio.create_subprocess_exec(
            *curl_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        task.update_progress(50, "Processing inference...")
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            task.update_progress(90, "Parsing response...")
            try:
                response_data = json.loads(stdout.decode("utf-8"))
                generated_text = response_data.get("response", "")
                result = {
                    "status": "success",
                    "message": f"Inference completed with model {model_name}",
                    "model_name": model_name,
                    "prompt": prompt,
                    "generated_text": generated_text,
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "generated_tokens": response_data.get("eval_count", 0),
                    "total_duration": response_data.get("eval_duration", 0),
                    "tokens_per_second": response_data.get("eval_count", 0)
                    / (response_data.get("eval_duration", 1) / 1000000000.0),
                }
                task.complete(result)
            except json.JSONDecodeError as e:
                task.fail(
                    f"Invalid JSON response from Ollama: {str(e)}",
                    TaskErrorCode.OLLAMA_ERROR,
                )
        else:
            error_msg = stderr.decode("utf-8").strip()
            task.fail(f"Ollama inference failed: {error_msg}")



