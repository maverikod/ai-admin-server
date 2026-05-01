"""Module queue_impl."""

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
from .enums import TaskErrorCode, TaskStatus, TaskType
from .task import Task

class MiscExecutor:
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

    async def _execute_custom_script_task(self, task: Task) -> None:
        """Execute custom script task."""
        import os

        params = task.params
        script_path = params.get("script_path", "")
        script_args = params.get("script_args", [])
        working_dir = params.get("working_dir", ".")
        task.update_progress(10, f"Starting custom script: {script_path}")
        if not os.path.exists(script_path):
            task.fail(
                f"Script not found: {script_path}",
                TaskErrorCode.DATA_FILE_NOT_FOUND,
                {"script_path": script_path},
            )
            return
        cmd = [script_path] + script_args
        task.command = " ".join(cmd)
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
            )
            task.update_progress(50, "Executing script...")
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                result = {
                    "status": "success",
                    "message": "Custom script executed successfully",
                    "script_path": script_path,
                    "stdout": stdout.decode("utf-8"),
                    "exit_code": process.returncode,
                }
                task.complete(result)
            else:
                error_msg = stderr.decode("utf-8").strip()
                task.fail(
                    f"Custom script failed: {error_msg}",
                    TaskErrorCode.CUSTOM_SCRIPT_FAILED,
                    {"exit_code": process.returncode, "stderr": error_msg},
                )
        except CustomError as e:
            task.fail(
                f"Exception during script execution: {str(e)}",
                TaskErrorCode.INTERNAL_ERROR,
                {"exception": str(e)},
            )

    async def _execute_custom_command_task(self, task: Task) -> None:
        """Execute custom command task."""
        params = task.params
        command = params.get("command", "")
        args = params.get("args", [])
        shell = params.get("shell", False)
        task.update_progress(10, f"Starting custom command: {command}")
        if not command:
            task.fail(
                "No command specified",
                TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                {"command": command},
            )
            return
        if shell:
            cmd = command
        else:
            cmd = [command] + args
        task.command = command if shell else " ".join(cmd)
        try:
            if shell:
                process = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
            task.update_progress(50, "Executing command...")
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                result = {
                    "status": "success",
                    "message": "Custom command executed successfully",
                    "command": command,
                    "stdout": stdout.decode("utf-8"),
                    "exit_code": process.returncode,
                }
                task.complete(result)
            else:
                error_msg = stderr.decode("utf-8").strip()
                task.fail(
                    f"Custom command failed: {error_msg}",
                    TaskErrorCode.CUSTOM_COMMAND_FAILED,
                    {"exit_code": process.returncode, "stderr": error_msg},
                )
        except CustomError as e:
            task.fail(
                f"Exception during command execution: {str(e)}",
                TaskErrorCode.INTERNAL_ERROR,
                {"exception": str(e)},
            )

    async def _execute_system_monitor_task(self, task: Task) -> None:
        """Execute system monitoring task using SystemMonitorCommand."""
        from ai_admin.commands.system_monitor_command import SystemMonitorCommand

        params = task.params
        operation_type = params.get("operation_type", "system_monitor")
        include_gpu = params.get("include_gpu", True)
        include_temperature = params.get("include_temperature", True)
        include_processes = params.get("include_processes", False)
        user_roles = params.get("user_roles", [])
        task.update_progress(10, f"Starting system monitoring: {operation_type}")
        try:
            system_monitor = SystemMonitorCommand()
            task.update_progress(25, "Initializing system monitor command")
            task.update_progress(50, "Collecting system metrics")
            result = await system_monitor.execute(
                include_gpu=include_gpu,
                include_temperature=include_temperature,
                include_processes=include_processes,
                user_roles=user_roles,
            )
            task.update_progress(75, "Processing system metrics")
            if hasattr(result, "success") and result.success:
                task.update_progress(90, "System monitoring completed successfully")
                task.complete(
                    {
                        "status": "success",
                        "message": "System monitoring completed",
                        "operation_type": operation_type,
                        "metrics": result.data.get("metrics", {}),
                        "user_roles": user_roles,
                        "ssl_enabled": True,
                    }
                )
            else:
                error_message = getattr(result, "message", "Unknown error")
                error_code = getattr(result, "code", "SYSTEM_MONITOR_ERROR")
                error_details = getattr(result, "details", {})
                task.fail(
                    f"System monitoring failed: {error_message}",
                    TaskErrorCode.SYSTEM_SERVICE_UNAVAILABLE,
                    {
                        "error_code": error_code,
                        "error_details": error_details,
                        "operation_type": operation_type,
                    },
                )
        except CustomError as e:
            task.fail(
                f"System monitoring task execution failed: {str(e)}",
                TaskErrorCode.SYSTEM_SERVICE_UNAVAILABLE,
                {
                    "exception": str(e),
                    "operation_type": operation_type,
                    "params": params,
                },
            )

    async def _execute_generic_task(self, task: Task) -> None:
        """Execute generic task with basic validation and execution."""
        params = task.params
        task_type = task.task_type.value
        task.update_progress(10, f"Starting generic task: {task_type}")
        try:
            if not params:
                task.fail(
                    "No parameters provided for generic task",
                    TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    {"task_type": task_type},
                )
                return
            task.update_progress(25, f"Processing {task_type} task...")
            if task_type == "custom_script":
                script_path = params.get("script_path", "")
                if not script_path:
                    task.fail(
                        "Script path not provided",
                        TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    )
                    return
                result = {
                    "status": "success",
                    "message": f"Custom script task completed",
                    "task_type": task_type,
                    "script_path": script_path,
                    "note": "Script execution handled by _execute_custom_script_task",
                }
            elif task_type == "custom_command":
                command = params.get("command", "")
                if not command:
                    task.fail(
                        "Command not provided",
                        TaskErrorCode.VALIDATION_MISSING_REQUIRED,
                    )
                    return
                result = {
                    "status": "success",
                    "message": f"Custom command task completed",
                    "task_type": task_type,
                    "command": command,
                    "note": "Command execution handled by _execute_custom_command_task",
                }
            else:
                task.fail(
                    f"Unknown task type: {task_type}",
                    TaskErrorCode.VALIDATION_INVALID_PARAMS,
                    {"task_type": task_type},
                )
                return
            task.update_progress(100, f"{task_type} task completed")
            task.complete(result)
        except CustomError as e:
            task.fail(
                f"Generic task failed: {str(e)}",
                TaskErrorCode.UNKNOWN_ERROR,
                {"exception": str(e), "task_type": task_type},
            )

    async def _execute_ssl_operation_task(self, task: Task) -> None:
        """Execute SSL operation task."""
        import logging
        from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand
        from ai_admin.commands.ssl_cert_view_command import SSLCertViewCommand
        from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand
        from ai_admin.commands.ssl_crl_command import SSLCrlCommand

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting SSL operation task {task.id} ===")
        params = task.params
        operation_type = params.get("operation_type")
        cert_type = params.get("cert_type", "self_signed")
        common_name = params.get("common_name", "localhost")
        ssl_config = params.get("ssl_config", {})
        user_roles = params.get("user_roles", [])
        logger.info(
            f"SSL operation parameters: operation_type={operation_type}, cert_type={cert_type}, common_name={common_name}"
        )
        task.update_progress(10, f"Starting SSL operation: {operation_type}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            if operation_type == "generate":
                task.update_progress(20, "Generating SSL certificate")
                command = SSLCertGenerateCommand()
                result = await command.execute(
                    cert_type=cert_type,
                    common_name=common_name,
                    user_roles=user_roles,
                    **ssl_config,
                )
            elif operation_type == "view":
                task.update_progress(20, "Viewing SSL certificate")
                command = SSLCertViewCommand()
                cert_path = params.get("cert_path")
                if not cert_path:
                    raise ValueError("cert_path is required for view operation")
                result = await command.execute(
                    cert_path=cert_path, user_roles=user_roles, **ssl_config
                )
            elif operation_type == "verify":
                task.update_progress(20, "Verifying SSL certificate")
                command = SSLCertVerifyCommand()
                cert_path = params.get("cert_path")
                if not cert_path:
                    raise ValueError("cert_path is required for verify operation")
                result = await command.execute(
                    cert_path=cert_path, user_roles=user_roles, **ssl_config
                )
            elif operation_type == "revoke":
                task.update_progress(20, "Managing CRL")
                command = SSLCrlCommand()
                action = params.get("action", "create")
                result = await command.execute(
                    action=action, user_roles=user_roles, **ssl_config
                )
            else:
                raise ValueError(f"Unsupported SSL operation: {operation_type}")
            if result.success:
                task.update_progress(
                    90, f"SSL operation {operation_type} completed successfully"
                )
                task.complete(
                    {
                        "message": f"SSL operation {operation_type} completed successfully",
                        "operation_type": operation_type,
                        "cert_type": cert_type,
                        "common_name": common_name,
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.SSL_OPERATION_FAILED, result.details
                )
        except CustomError as e:
            error_msg = f"SSL operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.SSL_OPERATION_FAILED, {"exception": str(e)}
            )

    async def _execute_vector_store_task(self, task: Task) -> None:
        """Execute Vector Store task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.vector_store_deploy_command import (
                VectorStoreDeployCommand,
            )

            task.update_progress(10, "Initializing Vector Store command")
            command = VectorStoreDeployCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(
                    90, "Vector Store operation completed successfully"
                )
                task.complete(
                    {
                        "message": "Vector Store operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message,
                    TaskErrorCode.VECTOR_STORE_OPERATION_FAILED,
                    result.details,
                )
        except CustomError as e:
            error_msg = f"Vector Store operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg,
                TaskErrorCode.VECTOR_STORE_OPERATION_FAILED,
                {"exception": str(e)},
            )

    async def _execute_llm_task(self, task: Task) -> None:
        """Execute LLM task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.llm_inference_command import LLMInferenceCommand

            task.update_progress(10, "Initializing LLM command")
            command = LLMInferenceCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(90, "LLM operation completed successfully")
                task.complete(
                    {
                        "message": "LLM operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.LLM_OPERATION_FAILED, result.details
                )
        except CustomError as e:
            error_msg = f"LLM operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.LLM_OPERATION_FAILED, {"exception": str(e)}
            )

    async def _execute_test_task(self, task: Task) -> None:
        """Execute Test task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.test_discovery_command import TestDiscoveryCommand

            task.update_progress(10, "Initializing Test command")
            command = TestDiscoveryCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(90, "Test operation completed successfully")
                task.complete(
                    {
                        "message": "Test operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.TEST_OPERATION_FAILED, result.details
                )
        except CustomError as e:
            error_msg = f"Test operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.TEST_OPERATION_FAILED, {"exception": str(e)}
            )

    async def _execute_argocd_task(self, task: Task) -> None:
        """Execute ArgoCD task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.argocd_init_command import ArgoCDInitCommand

            task.update_progress(10, "Initializing ArgoCD command")
            command = ArgoCDInitCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(90, "ArgoCD operation completed successfully")
                task.complete(
                    {
                        "message": "ArgoCD operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message,
                    TaskErrorCode.ARGOCD_OPERATION_FAILED,
                    result.details,
                )
        except CustomError as e:
            error_msg = f"ArgoCD operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.ARGOCD_OPERATION_FAILED, {"exception": str(e)}
            )

    async def _execute_ssh_task(self, task: Task) -> None:
        """Execute SSH task.

        Args:
            task: SSH task to execute
        """
        import logging

        logger = logging.getLogger(__name__)
        params = task.params.copy()
        user_roles = params.pop("user_roles", None)
        try:
            task.update_progress(5, "Initializing SSH operation")
            if task.task_type == TaskType.SSH_CONNECT:
                from ai_admin.commands.ssh_connect_command import SshConnectCommand

                task.update_progress(10, "Initializing SSH Connect command")
                command = SshConnectCommand()
                result = await command.execute(user_roles=user_roles, **params)
                if result.success:
                    task.update_progress(
                        90, "SSH Connect operation completed successfully"
                    )
                    task.complete(
                        {
                            "message": "SSH Connect operation completed successfully",
                            "result": result.data,
                        }
                    )
                else:
                    task.fail(
                        result.message, TaskErrorCode.SSH_CONNECT_ERROR, result.details
                    )
            elif task.task_type == TaskType.SSH_EXEC:
                from ai_admin.commands.ssh_exec_command import SshExecCommand

                task.update_progress(10, "Initializing SSH Exec command")
                command = SshExecCommand()
                result = await command.execute(user_roles=user_roles, **params)
                if result.success:
                    task.update_progress(
                        90, "SSH Exec operation completed successfully"
                    )
                    task.complete(
                        {
                            "message": "SSH Exec operation completed successfully",
                            "result": result.data,
                        }
                    )
                else:
                    task.fail(
                        result.message, TaskErrorCode.SSH_EXEC_ERROR, result.details
                    )
        except CustomError as e:
            error_msg = f"SSH operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.SSH_ERROR, {"exception": str(e)})

