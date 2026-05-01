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

class FtpExecutor:
    """Universal task queue for managing any type of operations."""

    def _create_ftp_connection(self, ftp_config: Dict[str, Any], task: Task) -> Any:
        """Create FTP connection with SSL/mTLS support.

        Args:
            ftp_config: FTP configuration dictionary
            task: Task object for logging

        Returns:
            FTP connection object
        """
        import ftplib
        import ssl

        host = ftp_config.get("host", "")
        user = ftp_config.get("user", "")
        password = ftp_config.get("password", "")
        port = ftp_config.get("port", 21)
        timeout = ftp_config.get("timeout", 30)
        ssl_config = ftp_config.get("ssl", {})
        ftp: Union[ftplib.FTP, ftplib.FTP_TLS]
        if ssl_config.get("enabled", False):
            if ssl_config.get("implicit", False):
                ftp = ftplib.FTP_TLS()
                ftp.connect(host, port, timeout=timeout)
                ftp.login(user, password)
                ftp.prot_p()
                task.add_log("DEBUG: Connected with implicit SSL/TLS")
            else:
                ftp = ftplib.FTP_TLS()
                ftp.connect(host, port, timeout=timeout)
                ftp.login(user, password)
                ftp.prot_p()
                task.add_log("DEBUG: Connected with explicit SSL/TLS")
            if ssl_config.get("cert_file") and ssl_config.get("key_file"):
                context = ssl.create_default_context()
                if ssl_config.get("ca_file"):
                    context.load_verify_locations(ssl_config["ca_file"])
                context.load_cert_chain(ssl_config["cert_file"], ssl_config["key_file"])
                if ftp.sock is not None:
                    ftp.sock = context.wrap_socket(ftp.sock, server_hostname=host)
                task.add_log("DEBUG: SSL certificates loaded")
        else:
            ftp = ftplib.FTP()
            ftp.connect(host, port, timeout=timeout)
            ftp.login(user, password)
            task.add_log("DEBUG: Connected with regular FTP")
        if ftp_config.get("passive_mode", True):
            ftp.set_pasv(True)
            task.add_log("DEBUG: Using passive mode")
        return ftp

    async def _execute_ftp_upload_task(self, task: Task) -> None:
        """Execute FTP upload task with resume support."""
        import ftplib
        import os
        import logging
        from pathlib import Path

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting FTP upload task {task.id} ===")
        params = task.params
        local_path = params.get("local_path", "")
        remote_path = params.get("remote_path", "")
        resume = params.get("resume", True)
        overwrite = params.get("overwrite", False)
        file_size = params.get("file_size", 0)
        logger.info(
            f"Upload parameters: local={local_path}, remote={remote_path}, resume={resume}, overwrite={overwrite}"
        )
        task.update_progress(5, f"Starting FTP upload: {os.path.basename(local_path)}")
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)},
                )
                return
            with open(config_path, "r") as f:
                config = json.load(f)
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config},
                )
                return
            task.update_progress(10, "Connecting to FTP server")
            task.add_log(f"DEBUG: Connecting to {host}:{ftp_config.get('port', 21)}")
            ftp = self._create_ftp_connection(ftp_config, task)
            task.update_progress(20, "Connected to FTP server")
            task.add_log(f"DEBUG: Successfully connected to {host}")
            remote_file_exists = False
            remote_file_size = 0
            try:
                if resume and (not overwrite):
                    remote_file_size = ftp.size(remote_path)
                    remote_file_exists = remote_file_size > 0
                    task.add_log(f"DEBUG: Remote file exists, size: {remote_file_size}")
            except ftplib.error_perm:
                remote_file_exists = False
                task.add_log(
                    "DEBUG: Remote file doesn't exist or no permission to check size"
                )
            if resume and remote_file_exists and (not overwrite):
                if remote_file_size >= file_size:
                    task.complete(
                        {
                            "message": "File already exists and is complete",
                            "local_path": local_path,
                            "remote_path": remote_path,
                            "file_size": file_size,
                            "remote_file_size": remote_file_size,
                            "resumed": False,
                            "uploaded_bytes": 0,
                        }
                    )
                    return
                task.update_progress(
                    30, f"Resuming upload from position {remote_file_size}"
                )
                task.add_log(f"DEBUG: Resuming upload from byte {remote_file_size}")
                with open(local_path, "rb") as local_file:
                    local_file.seek(remote_file_size)

                    def upload_callback(data: bytes) -> None:
                        nonlocal remote_file_size
                        remote_file_size += len(data)
                        progress = min(95, 30 + int(remote_file_size / file_size * 65))
                        task.update_progress(
                            progress, f"Uploading: {remote_file_size}/{file_size} bytes"
                        )

                    ftp.storbinary(
                        f"STOR {remote_path}",
                        local_file,
                        callback=upload_callback,
                        rest=remote_file_size,
                    )
            else:
                task.update_progress(30, "Starting full upload")
                task.add_log("DEBUG: Starting full upload")
                with open(local_path, "rb") as local_file:
                    uploaded_bytes = 0

                    def upload_callback(data: bytes) -> None:
                        nonlocal uploaded_bytes
                        uploaded_bytes += len(data)
                        progress = min(95, 30 + int(uploaded_bytes / file_size * 65))
                        task.update_progress(
                            progress, f"Uploading: {uploaded_bytes}/{file_size} bytes"
                        )

                    ftp.storbinary(
                        f"STOR {remote_path}", local_file, callback=upload_callback
                    )
                    uploaded_bytes = file_size
            task.update_progress(95, "Verifying upload")
            try:
                final_size = ftp.size(remote_path)
                if final_size != file_size:
                    task.fail(
                        f"Upload verification failed: expected {file_size}, got {final_size}",
                        TaskErrorCode.FTP_UPLOAD_FAILED,
                        {"expected_size": file_size, "actual_size": final_size},
                    )
                    return
            except ftplib.error_perm as e:
                task.fail(
                    f"Failed to verify upload: {str(e)}",
                    TaskErrorCode.FTP_UPLOAD_FAILED,
                    {"error": str(e)},
                )
                return
            ftp.quit()
            task.complete(
                {
                    "message": "FTP upload completed successfully",
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "file_size": file_size,
                    "uploaded_bytes": file_size,
                    "resumed": resume and remote_file_exists,
                    "resume_position": (
                        remote_file_size if resume and remote_file_exists else 0
                    ),
                }
            )
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except ftplib.error_temp as e:
            error_msg = f"FTP temporary error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except ftplib.error_proto as e:
            error_msg = f"FTP protocol error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except CustomError as e:
            error_msg = f"FTP upload failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_UPLOAD_FAILED, {"error": str(e)})

    async def _execute_ftp_download_task(self, task: Task) -> None:
        """Execute FTP download task with resume support."""
        import ftplib
        import os
        import logging
        from pathlib import Path

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting FTP download task {task.id} ===")
        params = task.params
        remote_path = params.get("remote_path", "")
        local_path = params.get("local_path", "")
        resume = params.get("resume", True)
        overwrite = params.get("overwrite", False)
        local_file_exists = params.get("local_file_exists", False)
        local_file_size = params.get("local_file_size", 0)
        logger.info(
            f"Download parameters: remote={remote_path}, local={local_path}, resume={resume}, overwrite={overwrite}"
        )
        task.update_progress(
            5, f"Starting FTP download: {os.path.basename(remote_path)}"
        )
        task.add_log(f"DEBUG: Task parameters: {params}")
        try:
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)},
                )
                return
            with open(config_path, "r") as f:
                config = json.load(f)
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config},
                )
                return
            task.update_progress(10, "Connecting to FTP server")
            task.add_log(f"DEBUG: Connecting to {host}:{ftp_config.get('port', 21)}")
            ftp = self._create_ftp_connection(ftp_config, task)
            task.update_progress(20, "Connected to FTP server")
            task.add_log(f"DEBUG: Successfully connected to {host}")
            try:
                remote_file_size = ftp.size(remote_path)
                if remote_file_size < 0:
                    task.fail(
                        "Remote file not found or no permission to access",
                        TaskErrorCode.FTP_FILE_NOT_FOUND,
                        {"remote_path": remote_path},
                    )
                    return
                task.add_log(f"DEBUG: Remote file size: {remote_file_size}")
            except ftplib.error_perm as e:
                task.fail(
                    f"Failed to get remote file size: {str(e)}",
                    TaskErrorCode.FTP_FILE_NOT_FOUND,
                    {"remote_path": remote_path, "error": str(e)},
                )
                return
            if resume and local_file_exists and (not overwrite):
                if local_file_size >= remote_file_size:
                    task.complete(
                        {
                            "message": "Local file already exists and is complete",
                            "local_path": local_path,
                            "remote_path": remote_path,
                            "file_size": remote_file_size,
                            "local_file_size": local_file_size,
                            "resumed": False,
                            "downloaded_bytes": 0,
                        }
                    )
                    return
                task.update_progress(
                    30, f"Resuming download from position {local_file_size}"
                )
                task.add_log(f"DEBUG: Resuming download from byte {local_file_size}")
                mode = "ab"
            else:
                task.update_progress(30, "Starting full download")
                task.add_log("DEBUG: Starting full download")
                mode = "wb"
                local_file_size = 0
            downloaded_bytes = local_file_size
            with open(local_path, mode) as local_file:

                def download_callback(data: bytes) -> None:
                    nonlocal downloaded_bytes
                    downloaded_bytes += len(data)
                    progress = min(
                        95, 30 + int(downloaded_bytes / remote_file_size * 65)
                    )
                    task.update_progress(
                        progress,
                        f"Downloading: {downloaded_bytes}/{remote_file_size} bytes",
                    )
                    local_file.write(data)

                ftp.retrbinary(
                    f"RETR {remote_path}", download_callback, rest=local_file_size
                )
            task.update_progress(95, "Verifying download")
            final_size = os.path.getsize(local_path)
            if final_size != remote_file_size:
                task.fail(
                    f"Download verification failed: expected {remote_file_size}, got {final_size}",
                    TaskErrorCode.FTP_DOWNLOAD_FAILED,
                    {"expected_size": remote_file_size, "actual_size": final_size},
                )
                return
            ftp.quit()
            task.complete(
                {
                    "message": "FTP download completed successfully",
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "file_size": remote_file_size,
                    "downloaded_bytes": final_size,
                    "resumed": resume and local_file_exists,
                    "resume_position": (
                        local_file_size if resume and local_file_exists else 0
                    ),
                }
            )
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except ftplib.error_temp as e:
            error_msg = f"FTP temporary error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except ftplib.error_proto as e:
            error_msg = f"FTP protocol error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})
        except CustomError as e:
            error_msg = f"FTP download failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_DOWNLOAD_FAILED, {"error": str(e)})

    async def _execute_ftp_list_task(self, task: Task) -> None:
        """Execute FTP list directory task."""
        import ftplib
        import logging
        import socket
        from pathlib import Path

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting FTP list task {task.id} ===")
        params = task.params
        remote_path = params.get("remote_path", "/")
        logger.info(f"List parameters: remote_path={remote_path}")
        task.update_progress(10, f"Listing directory: {remote_path}")
        try:
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)},
                )
                return
            with open(config_path, "r") as f:
                config = json.load(f)
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config},
                )
                return
            task.update_progress(30, "Connecting to FTP server")
            ftp = self._create_ftp_connection(ftp_config, task)
            task.update_progress(50, "Connected to FTP server")
            files = []
            ftp.retrlines("LIST", lambda line: files.append(line))
            task.update_progress(90, "Directory listing completed")
            ftp.quit()
            task.complete(
                {
                    "message": "FTP directory listing completed",
                    "remote_path": remote_path,
                    "files": files,
                    "file_count": len(files),
                }
            )
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except socket.timeout as e:
            error_msg = f"FTP timeout - possible firewall issue: {str(e)}"
            logger.error(error_msg)
            task.fail(
                error_msg,
                TaskErrorCode.FTP_CONNECTION_FAILED,
                {"error": str(e), "suggestion": "Check firewall settings"},
            )
        except NetworkError as e:
            error_msg = f"FTP list failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})

    async def _execute_ftp_delete_task(self, task: Task) -> None:
        """Execute FTP delete file task."""
        import ftplib
        import logging
        from pathlib import Path

        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        logger.info(f"=== Starting FTP delete task {task.id} ===")
        params = task.params
        remote_path = params.get("remote_path", "")
        logger.info(f"Delete parameters: remote_path={remote_path}")
        task.update_progress(10, f"Deleting file: {remote_path}")
        try:
            config_path = Path("config/config.json")
            if not config_path.exists():
                task.fail(
                    "FTP configuration file not found",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"config_path": str(config_path)},
                )
                return
            with open(config_path, "r") as f:
                config = json.load(f)
            ftp_config = config.get("ftp", {})
            host = ftp_config.get("host")
            user = ftp_config.get("user")
            password = ftp_config.get("password")
            if not all([host, user, password]):
                task.fail(
                    "FTP configuration incomplete",
                    TaskErrorCode.CONFIGURATION_ERROR,
                    {"ftp_config": ftp_config},
                )
                return
            task.update_progress(30, "Connecting to FTP server")
            ftp = self._create_ftp_connection(ftp_config, task)
            task.update_progress(50, "Connected to FTP server")
            ftp.delete(remote_path)
            task.update_progress(90, "File deleted successfully")
            ftp.quit()
            task.complete(
                {"message": "FTP file deletion completed", "remote_path": remote_path}
            )
        except ftplib.error_perm as e:
            error_msg = f"FTP permission error: {str(e)}"
            logger.error(error_msg)
            task.fail(error_msg, TaskErrorCode.FTP_PERMISSION_DENIED, {"error": str(e)})
        except NetworkError as e:
            error_msg = f"FTP delete failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail(error_msg, TaskErrorCode.FTP_CONNECTION_FAILED, {"error": str(e)})



