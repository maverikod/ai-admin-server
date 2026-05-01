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

class DockerExecutor:
    """Universal task queue for managing any type of operations."""

    async def _execute_docker_push_task(self, task: Task) -> None:
        """Execute Docker push task."""
        import logging
        from ai_admin.security.docker_security_adapter import (
            DockerSecurityAdapter,
            DockerOperation,
        )

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Docker push task {task.id} ===")
        params = task.params
        image_name = params.get("image_name", "")
        tag = params.get("tag", "latest")
        full_image_name = f"{image_name}:{tag}"
        user_roles = params.get("user_roles", [])
        logger.info(
            f"Push parameters: image_name={image_name}, tag={tag}, full_name={full_image_name}"
        )
        security_adapter = DockerSecurityAdapter()
        operation_params = {
            "image_name": image_name,
            "tag": tag,
            "all_tags": params.get("all_tags", False),
            "disable_content_trust": params.get("disable_content_trust", False),
            "quiet": params.get("quiet", False),
        }
        is_valid, error_msg = security_adapter.validate_docker_operation(
            DockerOperation.PUSH, user_roles, operation_params
        )
        if not is_valid:
            error_msg = f"Security validation failed: {error_msg}"
            logger.error(error_msg)
            task.add_log(f"SECURITY ERROR: {error_msg}")
            task.fail(error_msg, TaskErrorCode.SECURITY_ERROR, {"error": error_msg})
            return
        task.update_progress(10, f"Starting push of {full_image_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        cmd = ["docker", "push", full_image_name]
        task.command = " ".join(cmd)
        logger.info(f"Executing command: {' '.join(cmd)}")
        task.add_log(f"DEBUG: Executing command: {' '.join(cmd)}")
        try:
            check_cmd = [
                "docker",
                "images",
                "--format",
                "{{.Repository}}:{{.Tag}}",
                full_image_name,
            ]
            logger.info(f"Checking image existence: {' '.join(check_cmd)}")
            task.add_log(f"DEBUG: Checking image existence: {' '.join(check_cmd)}")
            check_process = await asyncio.create_subprocess_exec(
                *check_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            check_stdout, check_stderr = await check_process.communicate()
            if (
                check_process.returncode != 0
                or not check_stdout.decode("utf-8").strip()
            ):
                error_msg = f"Image {full_image_name} not found locally"
                logger.error(error_msg)
                task.add_log(f"DEBUG: {error_msg}")
                task.fail(
                    error_msg,
                    TaskErrorCode.DOCKER_IMAGE_NOT_FOUND,
                    {
                        "image_name": full_image_name,
                        "check_command": " ".join(check_cmd),
                    },
                )
                return
            logger.info(f"Image {full_image_name} found locally")
            task.add_log(f"DEBUG: Image {full_image_name} found locally")
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            logger.info(f"Process started with PID: {process.pid}")
            task.add_log(f"DEBUG: Process started with PID: {process.pid}")
            task.update_progress(25, "Pushing layers...")
            stdout, stderr = await process.communicate()
            logger.info(f"Process completed with return code: {process.returncode}")
            task.add_log(
                f"DEBUG: Process completed with return code: {process.returncode}"
            )
            if stdout:
                logger.info(f"STDOUT: {stdout.decode('utf-8')}")
                task.add_log(f"DEBUG: STDOUT: {stdout.decode('utf-8')}")
            if stderr:
                logger.warning(f"STDERR: {stderr.decode('utf-8')}")
                task.add_log(f"DEBUG: STDERR: {stderr.decode('utf-8')}")
            if process.returncode == 0:
                task.update_progress(90, "Finalizing push...")
                output_lines = stdout.decode("utf-8").splitlines()
                digest = None
                for line in output_lines:
                    if "digest:" in line:
                        digest = line.split("digest: ")[-1].strip()
                        break
                security_adapter.audit_docker_operation(
                    DockerOperation.PUSH, user_roles, operation_params, "executed"
                )
                result = {
                    "status": "success",
                    "message": "Docker image pushed successfully",
                    "image_name": image_name,
                    "tag": tag,
                    "full_image_name": full_image_name,
                    "digest": digest,
                }
                logger.info(f"Push completed successfully: {result}")
                task.add_log(f"DEBUG: Push completed successfully: {result}")
                task.complete(result)
            else:
                error_msg = stderr.decode("utf-8").strip()
                logger.error(f"Push failed: {error_msg}")
                task.add_log(f"DEBUG: Push failed: {error_msg}")
                error_code = TaskErrorCode.DOCKER_PUSH_FAILED
                error_details = {
                    "exit_code": process.returncode,
                    "stderr": error_msg,
                    "command": " ".join(cmd),
                }
                if "denied" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_PERMISSION_DENIED
                elif "authentication" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_AUTHENTICATION_FAILED
                elif (
                    "network" in error_msg.lower() or "connection" in error_msg.lower()
                ):
                    error_code = TaskErrorCode.DOCKER_NETWORK_ERROR
                elif "registry" in error_msg.lower():
                    error_code = TaskErrorCode.DOCKER_REGISTRY_ERROR
                security_adapter.audit_docker_operation(
                    DockerOperation.PUSH, user_roles, operation_params, "failed"
                )
                task.fail(f"Docker push failed: {error_msg}", error_code, error_details)
        except CustomError as e:
            error_msg = f"Exception during push: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.add_log(f"DEBUG: Exception during push: {str(e)}")
            security_adapter.audit_docker_operation(
                DockerOperation.PUSH, user_roles, operation_params, "failed"
            )
            task.fail(
                error_msg,
                TaskErrorCode.INTERNAL_ERROR,
                {"exception_type": type(e).__name__, "exception": str(e)},
            )
        logger.info(f"=== Completed Docker push task {task.id} ===")

    async def _execute_docker_build_task(self, task: Task) -> None:
        """Execute Docker build task."""
        import logging
        from ai_admin.security.docker_security_adapter import (
            DockerSecurityAdapter,
            DockerOperation,
        )

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Docker build task {task.id} ===")
        params = task.params
        context_path = params.get("context_path", ".")
        dockerfile = params.get("dockerfile", "Dockerfile")
        tag = params.get("tag", "latest")
        image_name = params.get("image_name", "")
        no_cache = params.get("no_cache", False)
        build_args = params.get("build_args", {})
        user_roles = params.get("user_roles", [])
        full_image_name = f"{image_name}:{tag}" if image_name else tag
        logger.info(
            f"Build parameters: context={context_path}, dockerfile={dockerfile}, tag={full_image_name}"
        )
        security_adapter = DockerSecurityAdapter()
        operation_params = {
            "dockerfile_path": dockerfile,
            "tag": tag,
            "context_path": context_path,
            "build_args": build_args,
            "no_cache": no_cache,
            "platform": params.get("platform"),
            "target": params.get("target"),
        }
        is_valid, error_msg = security_adapter.validate_docker_operation(
            DockerOperation.BUILD, user_roles, operation_params
        )
        if not is_valid:
            error_msg = f"Security validation failed: {error_msg}"
            logger.error(error_msg)
            task.add_log(f"SECURITY ERROR: {error_msg}")
            task.fail(error_msg, TaskErrorCode.SECURITY_ERROR, {"error": error_msg})
            return
        task.update_progress(10, f"Starting build of {full_image_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        cmd = ["docker", "build"]
        if no_cache:
            cmd.append("--no-cache")
        if build_args:
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
        cmd.extend(["-t", full_image_name, "-f", dockerfile, context_path])
        task.command = " ".join(cmd)
        logger.info(f"Executing command: {' '.join(cmd)}")
        task.add_log(f"DEBUG: Executing command: {' '.join(cmd)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=context_path,
            )
            task.update_progress(25, "Building image layers...")
            stdout, stderr = await process.communicate()
            logger.info(f"Process completed with return code: {process.returncode}")
            task.add_log(
                f"DEBUG: Process completed with return code: {process.returncode}"
            )
            if process.returncode == 0:
                task.update_progress(90, "Finalizing build...")
                output_lines = stdout.decode("utf-8").splitlines()
                build_info = []
                for line in output_lines:
                    if "Successfully built" in line:
                        build_info.append(line.strip())
                    elif "Step" in line and ":" in line:
                        build_info.append(line.strip())
                logger.info(f"Build completed successfully")
                task.add_log(f"DEBUG: STDOUT: {stdout.decode('utf-8')}")
                security_adapter.audit_docker_operation(
                    DockerOperation.BUILD, user_roles, operation_params, "executed"
                )
                result = {
                    "status": "success",
                    "message": "Docker image built successfully",
                    "image_name": full_image_name,
                    "context_path": context_path,
                    "dockerfile": dockerfile,
                    "build_info": build_info,
                    "command": " ".join(cmd),
                }
                task.update_progress(100, "Build completed successfully")
                task.complete(result)
            else:
                error_output = stderr.decode("utf-8")
                logger.error(f"Build failed: {error_output}")
                task.add_log(f"DEBUG: STDERR: {error_output}")
                security_adapter.audit_docker_operation(
                    DockerOperation.BUILD, user_roles, operation_params, "failed"
                )
                task.fail(
                    f"Docker build failed: {error_output}",
                    "DOCKER_BUILD_FAILED",
                    {
                        "exit_code": process.returncode,
                        "stderr": error_output,
                        "command": " ".join(cmd),
                    },
                )
        except CustomError as e:
            error_msg = f"Docker build failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            security_adapter.audit_docker_operation(
                DockerOperation.BUILD, user_roles, operation_params, "failed"
            )
            task.fail(error_msg, TaskErrorCode.DOCKER_BUILD_FAILED, {"error": str(e)})

    async def _execute_docker_pull_task(self, task: Task) -> None:
        """Execute Docker pull task."""
        import logging
        from ai_admin.security.docker_security_adapter import (
            DockerSecurityAdapter,
            DockerOperation,
        )

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting Docker pull task {task.id} ===")
        params = task.params
        image_name = params.get("image_name", "")
        tag = params.get("tag", "latest")
        user_roles = params.get("user_roles", [])
        if ":" in image_name:
            full_image_name = image_name
        else:
            full_image_name = f"{image_name}:{tag}"
        logger.info(
            f"Pull parameters: image_name={image_name}, tag={tag}, full_name={full_image_name}"
        )
        security_adapter = DockerSecurityAdapter()
        operation_params = {
            "image_name": image_name,
            "tag": tag,
            "all_tags": params.get("all_tags", False),
            "disable_content_trust": params.get("disable_content_trust", False),
            "quiet": params.get("quiet", False),
            "platform": params.get("platform"),
        }
        is_valid, error_msg = security_adapter.validate_docker_operation(
            DockerOperation.PULL, user_roles, operation_params
        )
        if not is_valid:
            error_msg = f"Security validation failed: {error_msg}"
            logger.error(error_msg)
            task.add_log(f"SECURITY ERROR: {error_msg}")
            task.fail(error_msg, TaskErrorCode.SECURITY_ERROR, {"error": error_msg})
            return
        task.update_progress(10, f"Starting pull of {full_image_name}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        cmd = ["docker", "pull", full_image_name]
        task.command = " ".join(cmd)
        logger.info(f"Executing command: {' '.join(cmd)}")
        task.add_log(f"DEBUG: Executing command: {' '.join(cmd)}")
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            task.update_progress(25, "Downloading layers...")
            stdout, stderr = await process.communicate()
            logger.info(f"Process completed with return code: {process.returncode}")
            task.add_log(
                f"DEBUG: Process completed with return code: {process.returncode}"
            )
            if process.returncode == 0:
                task.update_progress(90, "Finalizing pull...")
                output_lines = stdout.decode("utf-8").splitlines()
                digest = None
                size_info = []
                for line in output_lines:
                    if "digest:" in line:
                        digest = line.split("digest: ")[-1].strip()
                    elif "Pulled" in line or "Mounted" in line:
                        size_info.append(line.strip())
                logger.info(f"Pull completed successfully: {digest}")
                task.add_log(f"DEBUG: STDOUT: {stdout.decode('utf-8')}")
                security_adapter.audit_docker_operation(
                    DockerOperation.PULL, user_roles, operation_params, "executed"
                )
                result = {
                    "status": "success",
                    "message": "Docker image pulled successfully",
                    "image_name": image_name,
                    "tag": tag,
                    "full_image_name": full_image_name,
                    "digest": digest,
                    "size_info": size_info,
                    "command": " ".join(cmd),
                }
                task.update_progress(100, "Pull completed successfully")
                task.complete(result)
            else:
                error_output = stderr.decode("utf-8")
                logger.error(f"Pull failed: {error_output}")
                task.add_log(f"DEBUG: STDERR: {error_output}")
                if (
                    "already up to date" in error_output.lower()
                    or "image is up to date" in error_output.lower()
                ):
                    security_adapter.audit_docker_operation(
                        DockerOperation.PULL, user_roles, operation_params, "executed"
                    )
                    result = {
                        "status": "success",
                        "message": "Docker image already up to date",
                        "image_name": image_name,
                        "tag": tag,
                        "full_image_name": full_image_name,
                        "command": " ".join(cmd),
                    }
                    task.complete(result)
                else:
                    security_adapter.audit_docker_operation(
                        DockerOperation.PULL, user_roles, operation_params, "failed"
                    )
                    task.fail(
                        f"Docker pull failed: {error_output}",
                        "DOCKER_PULL_FAILED",
                        {
                            "exit_code": process.returncode,
                            "stderr": error_output,
                            "command": " ".join(cmd),
                        },
                    )
        except CustomError as e:
            error_msg = f"Docker pull failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            security_adapter.audit_docker_operation(
                DockerOperation.PULL, user_roles, operation_params, "failed"
            )
            task.fail(error_msg, TaskErrorCode.DOCKER_PULL_FAILED, {"error": str(e)})

    async def _execute_docker_network_task(self, task: Task) -> None:
        """Execute Docker Network task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            action = params.get("action", "list")
            task.update_progress(10, f"Initializing Docker Network {action} command")
            if action == "ls":
                from ai_admin.commands.docker_network_ls_command import (
                    DockerNetworkLsCommand,
                )

                command = DockerNetworkLsCommand()
            elif action == "inspect":
                from ai_admin.commands.docker_network_inspect_command import (
                    DockerNetworkInspectCommand,
                )

                command = DockerNetworkInspectCommand()
            elif action == "create":
                from ai_admin.commands.docker_network_create_command import (
                    DockerNetworkCreateCommand,
                )

                command = DockerNetworkCreateCommand()
            elif action == "connect":
                from ai_admin.commands.docker_network_connect_command import (
                    DockerNetworkConnectCommand,
                )

                command = DockerNetworkConnectCommand()
            elif action == "disconnect":
                from ai_admin.commands.docker_network_disconnect_command import (
                    DockerNetworkDisconnectCommand,
                )

                command = DockerNetworkDisconnectCommand()
            elif action == "rm":
                from ai_admin.commands.docker_network_rm_command import (
                    DockerNetworkRmCommand,
                )

                command = DockerNetworkRmCommand()
            else:
                raise ValueError(f"Unsupported Docker Network action: {action}")
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(
                    90, f"Docker Network {action} operation completed successfully"
                )
                task.complete(
                    {
                        "message": f"Docker Network {action} operation completed successfully",
                        "action": action,
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.DOCKER_NETWORK_ERROR, result.details
                )
        except NetworkError as e:
            error_msg = f"Docker Network operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.DOCKER_NETWORK_ERROR, {"exception": str(e)}
            )

    async def _execute_docker_volume_task(self, task: Task) -> None:
        """Execute Docker Volume task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.docker_volume_command import DockerVolumeCommand

            task.update_progress(10, "Initializing Docker Volume command")
            command = DockerVolumeCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(
                    90, "Docker Volume operation completed successfully"
                )
                task.complete(
                    {
                        "message": "Docker Volume operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.DOCKER_VOLUME_ERROR, result.details
                )
        except CustomError as e:
            error_msg = f"Docker Volume operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.DOCKER_VOLUME_ERROR, {"exception": str(e)}
            )

    async def _execute_docker_search_task(self, task: Task) -> None:
        """Execute Docker Search task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.docker_search_cli_command import (
                DockerSearchCliCommand,
            )

            task.update_progress(10, "Initializing Docker Search command")
            command = DockerSearchCliCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(
                    90, "Docker Search operation completed successfully"
                )
                task.complete(
                    {
                        "message": "Docker Search operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.DOCKER_SEARCH_ERROR, result.details
                )
        except CustomError as e:
            error_msg = f"Docker Search operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(
                error_msg, TaskErrorCode.DOCKER_SEARCH_ERROR, {"exception": str(e)}
            )

    async def _execute_docker_hub_task(self, task: Task) -> None:
        """Execute Docker Hub task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.docker_hub_images_command import (
                DockerHubImagesCommand,
            )

            task.update_progress(10, "Initializing Docker Hub command")
            command = DockerHubImagesCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(90, "Docker Hub operation completed successfully")
                task.complete(
                    {
                        "message": "Docker Hub operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.DOCKER_HUB_ERROR, result.details
                )
        except CustomError as e:
            error_msg = f"Docker Hub operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.DOCKER_HUB_ERROR, {"exception": str(e)})

    async def _execute_docker_tag_task(self, task: Task) -> None:
        """Execute Docker Tag task."""
        import logging

        logger = logging.getLogger(__name__)
        try:
            params = task.params
            user_roles = params.get("user_roles", ["default"])
            from ai_admin.commands.docker_tag_command import DockerTagCommand

            task.update_progress(10, "Initializing Docker Tag command")
            command = DockerTagCommand()
            result = await command.execute(user_roles=user_roles, **params)
            if result.success:
                task.update_progress(90, "Docker Tag operation completed successfully")
                task.complete(
                    {
                        "message": "Docker Tag operation completed successfully",
                        "result": result.data,
                    }
                )
            else:
                task.fail(
                    result.message, TaskErrorCode.DOCKER_TAG_ERROR, result.details
                )
        except CustomError as e:
            error_msg = f"Docker Tag operation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.DOCKER_TAG_ERROR, {"exception": str(e)})



