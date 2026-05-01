"""
FTP Client with support for active/passive modes and FTPS

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import os
import ssl
import logging
import stat
from typing import Optional, Dict, Any, List, BinaryIO, Callable
from ftplib import FTP, FTP_TLS, error_perm, error_temp
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class FTPClient:
    """Enhanced FTP client with active/passive modes and FTPS support."""

    def __init__(
        self,
        host: str,
        port: int = 21,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ftps: bool = False,
        passive_mode: bool = True,
        timeout: int = 30,
        ssl_context: Optional[ssl.SSLContext] = None,
    ):
        """
        Initialize FTP client.

        Args:
            host: FTP server hostname
            port: FTP server port (default: 21, FTPS: 990)
            username: FTP username
            password: FTP password
            use_ftps: Use FTPS (FTP over SSL/TLS)
            passive_mode: Use passive mode (True) or active mode (False)
            timeout: Connection timeout in seconds
            ssl_context: Custom SSL context for FTPS
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ftps = use_ftps
        self.passive_mode = passive_mode
        self.timeout = timeout
        self.ssl_context = ssl_context
        self.ftp: Optional[FTP] = None
        self.connected = False

    def _create_ftp_connection(self) -> FTP:
        """Create FTP or FTPS connection."""
        if self.use_ftps:
            if self.ssl_context:
                ftp = FTP_TLS(context=self.ssl_context)
            else:
                ftp = FTP_TLS()
            logger.info(f"Creating FTPS connection to {self.host}:{self.port}")
        else:
            ftp = FTP()
            logger.info(f"Creating FTP connection to {self.host}:{self.port}")

        ftp.set_debuglevel(0)  # Set to 1 for debug output
        return ftp

    def connect(self) -> None:
        """Connect to FTP server."""
        try:
            self.ftp = self._create_ftp_connection()
            self.ftp.connect(self.host, self.port, timeout=self.timeout)
            
            if self.username and self.password:
                self.ftp.login(self.username, self.password)
            elif self.username:
                self.ftp.login(self.username)
            else:
                self.ftp.login()  # Anonymous login

            # Set passive/active mode
            if self.passive_mode:
                self.ftp.set_pasv(True)
                logger.info("FTP passive mode enabled")
            else:
                self.ftp.set_pasv(False)
                logger.info("FTP active mode enabled")

            # For FTPS, protect data connection
            if self.use_ftps and isinstance(self.ftp, FTP_TLS):
                self.ftp.prot_p()  # Protect data connection
                logger.info("FTPS data connection protected")

            self.connected = True
            logger.info(f"Successfully connected to FTP server {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Failed to connect to FTP server: {e}")
            self.connected = False
            raise

    def disconnect(self) -> None:
        """Disconnect from FTP server."""
        if self.ftp and self.connected:
            try:
                self.ftp.quit()
                logger.info("FTP connection closed gracefully")
            except Exception as e:
                logger.warning(f"Error closing FTP connection: {e}")
                try:
                    self.ftp.close()
                except:
                    pass
            finally:
                self.connected = False
                self.ftp = None

    @contextmanager
    def connection(self):
        """Context manager for FTP connection."""
        try:
            self.connect()
            yield self
        finally:
            self.disconnect()

    def list_files(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        List files and directories in the specified path.

        Args:
            path: Remote directory path

        Returns:
            List of file/directory information dictionaries
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            files = []
            self.ftp.cwd(path)
            
            def parse_line(line: str) -> Dict[str, Any]:
                """Parse FTP LIST output line."""
                parts = line.split()
                if len(parts) < 9:
                    return {"name": line, "type": "unknown"}
                
                # Parse permissions
                permissions = parts[0]
                file_type = "directory" if permissions.startswith("d") else "file"
                
                # Parse size
                try:
                    size = int(parts[4])
                except (ValueError, IndexError):
                    size = 0
                
                # Parse date and time
                date_parts = parts[5:8]
                date_str = " ".join(date_parts) if len(date_parts) >= 3 else "unknown"
                
                # Parse filename
                filename = " ".join(parts[8:]) if len(parts) > 8 else "unknown"
                
                return {
                    "name": filename,
                    "type": file_type,
                    "size": size,
                    "permissions": permissions,
                    "date": date_str,
                    "path": f"{path.rstrip('/')}/{filename}" if path != "/" else f"/{filename}"
                }

            # Use retrlines for better compatibility with passive mode
            self.ftp.retrlines("LIST", lambda line: files.append(parse_line(line)))
            
            logger.info(f"Listed {len(files)} items in {path}")
            return files

        except Exception as e:
            logger.error(f"Failed to list files in {path}: {e}")
            raise

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        resume: bool = False,
        overwrite: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to FTP server.

        Args:
            local_path: Local file path
            remote_path: Remote file path
            resume: Resume interrupted upload
            overwrite: Overwrite existing file
            progress_callback: Callback function for progress updates

        Returns:
            Upload result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        try:
            # Check if remote file exists
            remote_exists = False
            try:
                self.ftp.size(remote_path)
                remote_exists = True
            except:
                pass

            if remote_exists and not overwrite and not resume:
                raise FileExistsError(f"Remote file exists and overwrite=False: {remote_path}")

            # Get file size for progress tracking
            file_size = os.path.getsize(local_path)
            uploaded_size = 0

            if resume and remote_exists:
                try:
                    uploaded_size = self.ftp.size(remote_path)
                    if uploaded_size >= file_size:
                        logger.info(f"File already fully uploaded: {remote_path}")
                        return {
                            "status": "completed",
                            "local_path": local_path,
                            "remote_path": remote_path,
                            "size": file_size,
                            "uploaded_size": uploaded_size,
                            "resumed": True
                        }
                except:
                    uploaded_size = 0

            # Upload file
            with open(local_path, "rb") as local_file:
                if resume and uploaded_size > 0:
                    local_file.seek(uploaded_size)
                    logger.info(f"Resuming upload from byte {uploaded_size}")

                def upload_callback(data: bytes) -> None:
                    nonlocal uploaded_size
                    uploaded_size += len(data)
                    if progress_callback:
                        progress = (uploaded_size / file_size) * 100
                        progress_callback(progress, uploaded_size, file_size)

                if resume and uploaded_size > 0:
                    # For resume, we need to use REST command
                    self.ftp.voidcmd(f"REST {uploaded_size}")
                    self.ftp.storbinary(f"STOR {remote_path}", local_file, callback=upload_callback)
                else:
                    self.ftp.storbinary(f"STOR {remote_path}", local_file, callback=upload_callback)

            logger.info(f"Successfully uploaded {local_path} to {remote_path}")
            return {
                "status": "completed",
                "local_path": local_path,
                "remote_path": remote_path,
                "size": file_size,
                "uploaded_size": uploaded_size,
                "resumed": resume and uploaded_size > 0
            }

        except Exception as e:
            logger.error(f"Failed to upload {local_path} to {remote_path}: {e}")
            raise

    def download_file(
        self,
        remote_path: str,
        local_path: str,
        resume: bool = False,
        overwrite: bool = False,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """
        Download file from FTP server.

        Args:
            remote_path: Remote file path
            local_path: Local file path
            resume: Resume interrupted download
            overwrite: Overwrite existing local file
            progress_callback: Callback function for progress updates

        Returns:
            Download result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            # Check if remote file exists
            try:
                remote_size = self.ftp.size(remote_path)
            except:
                raise FileNotFoundError(f"Remote file not found: {remote_path}")

            # Check local file
            local_exists = os.path.exists(local_path)
            downloaded_size = 0

            if local_exists and not overwrite and not resume:
                raise FileExistsError(f"Local file exists and overwrite=False: {local_path}")

            if resume and local_exists:
                downloaded_size = os.path.getsize(local_path)
                if downloaded_size >= remote_size:
                    logger.info(f"File already fully downloaded: {local_path}")
                    return {
                        "status": "completed",
                        "remote_path": remote_path,
                        "local_path": local_path,
                        "size": remote_size,
                        "downloaded_size": downloaded_size,
                        "resumed": True
                    }

            # Download file
            mode = "ab" if resume and downloaded_size > 0 else "wb"
            with open(local_path, mode) as local_file:
                if resume and downloaded_size > 0:
                    logger.info(f"Resuming download from byte {downloaded_size}")

                def download_callback(data: bytes) -> None:
                    nonlocal downloaded_size
                    downloaded_size += len(data)
                    if progress_callback:
                        progress = (downloaded_size / remote_size) * 100
                        progress_callback(progress, downloaded_size, remote_size)

                if resume and downloaded_size > 0:
                    # For resume, we need to use REST command
                    self.ftp.voidcmd(f"REST {downloaded_size}")
                    self.ftp.retrbinary(f"RETR {remote_path}", local_file.write, callback=download_callback)
                else:
                    self.ftp.retrbinary(f"RETR {remote_path}", local_file.write, callback=download_callback)

            logger.info(f"Successfully downloaded {remote_path} to {local_path}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "local_path": local_path,
                "size": remote_size,
                "downloaded_size": downloaded_size,
                "resumed": resume and downloaded_size > 0
            }

        except Exception as e:
            logger.error(f"Failed to download {remote_path} to {local_path}: {e}")
            raise

    def delete_file(self, remote_path: str) -> Dict[str, Any]:
        """
        Delete file from FTP server.

        Args:
            remote_path: Remote file path to delete

        Returns:
            Delete result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            # Check if file exists
            try:
                self.ftp.size(remote_path)
            except:
                raise FileNotFoundError(f"Remote file not found: {remote_path}")

            self.ftp.delete(remote_path)
            logger.info(f"Successfully deleted {remote_path}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "deleted": True
            }

        except Exception as e:
            logger.error(f"Failed to delete {remote_path}: {e}")
            raise

    def create_directory(self, remote_path: str) -> Dict[str, Any]:
        """
        Create directory on FTP server.

        Args:
            remote_path: Remote directory path to create

        Returns:
            Create directory result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            self.ftp.mkd(remote_path)
            logger.info(f"Successfully created directory {remote_path}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "created": True
            }

        except Exception as e:
            logger.error(f"Failed to create directory {remote_path}: {e}")
            raise

    def remove_directory(self, remote_path: str) -> Dict[str, Any]:
        """
        Remove directory from FTP server.

        Args:
            remote_path: Remote directory path to remove

        Returns:
            Remove directory result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            self.ftp.rmd(remote_path)
            logger.info(f"Successfully removed directory {remote_path}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "removed": True
            }

        except Exception as e:
            logger.error(f"Failed to remove directory {remote_path}: {e}")
            raise

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get FTP server information.

        Returns:
            Server information dictionary
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            welcome_msg = self.ftp.getwelcome()
            return {
                "host": self.host,
                "port": self.port,
                "use_ftps": self.use_ftps,
                "passive_mode": self.passive_mode,
                "welcome_message": welcome_msg,
                "connected": self.connected
            }

        except Exception as e:
            logger.error(f"Failed to get server info: {e}")
            raise

    def change_directory(self, remote_path: str) -> Dict[str, Any]:
        """
        Change current directory on FTP server.

        Args:
            remote_path: Remote directory path

        Returns:
            Change directory result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            self.ftp.cwd(remote_path)
            current_dir = self.ftp.pwd()
            logger.info(f"Changed directory to {current_dir}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "current_directory": current_dir
            }

        except Exception as e:
            logger.error(f"Failed to change directory to {remote_path}: {e}")
            raise

    def get_current_directory(self) -> str:
        """
        Get current directory on FTP server.

        Returns:
            Current directory path
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            return self.ftp.pwd()
        except Exception as e:
            logger.error(f"Failed to get current directory: {e}")
            raise

    def get_file_size(self, remote_path: str) -> int:
        """
        Get file size on FTP server.

        Args:
            remote_path: Remote file path

        Returns:
            File size in bytes
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            return self.ftp.size(remote_path)
        except Exception as e:
            logger.error(f"Failed to get file size for {remote_path}: {e}")
            raise

    def get_file_info(self, remote_path: str) -> Dict[str, Any]:
        """
        Get detailed file information.

        Args:
            remote_path: Remote file path

        Returns:
            File information dictionary
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            size = self.ftp.size(remote_path)
            mdtm = self.ftp.voidcmd(f"MDTM {remote_path}")
            return {
                "path": remote_path,
                "size": size,
                "modified_time": mdtm,
                "exists": True
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {remote_path}: {e}")
            raise

    def rename_file(self, old_path: str, new_path: str) -> Dict[str, Any]:
        """
        Rename file on FTP server.

        Args:
            old_path: Current file path
            new_path: New file path

        Returns:
            Rename result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            self.ftp.rename(old_path, new_path)
            logger.info(f"Successfully renamed {old_path} to {new_path}")
            return {
                "status": "completed",
                "old_path": old_path,
                "new_path": new_path,
                "renamed": True
            }

        except Exception as e:
            logger.error(f"Failed to rename {old_path} to {new_path}: {e}")
            raise

    def set_file_permissions(self, remote_path: str, permissions: str) -> Dict[str, Any]:
        """
        Set file permissions on FTP server.

        Args:
            remote_path: Remote file path
            permissions: Unix-style permissions (e.g., "755", "644")

        Returns:
            Set permissions result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            self.ftp.voidcmd(f"SITE CHMOD {permissions} {remote_path}")
            logger.info(f"Successfully set permissions {permissions} for {remote_path}")
            return {
                "status": "completed",
                "remote_path": remote_path,
                "permissions": permissions,
                "set": True
            }

        except Exception as e:
            logger.error(f"Failed to set permissions for {remote_path}: {e}")
            raise

    def upload_directory(
        self,
        local_dir: str,
        remote_dir: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Upload entire directory recursively.

        Args:
            local_dir: Local directory path
            remote_dir: Remote directory path
            progress_callback: Callback function for progress updates

        Returns:
            Upload directory result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        if not os.path.isdir(local_dir):
            raise NotADirectoryError(f"Local path is not a directory: {local_dir}")

        try:
            # Create remote directory
            try:
                self.ftp.mkd(remote_dir)
            except error_perm:
                pass  # Directory might already exist

            uploaded_files = []
            total_files = 0
            uploaded_count = 0

            # Count total files first
            for root, dirs, files in os.walk(local_dir):
                total_files += len(files)

            # Upload files
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(local_file_path, local_dir)
                    remote_file_path = f"{remote_dir}/{rel_path}".replace("\\", "/")

                    # Create subdirectories if needed
                    remote_subdir = os.path.dirname(remote_file_path)
                    if remote_subdir != remote_dir:
                        try:
                            self.ftp.mkd(remote_subdir)
                        except error_perm:
                            pass

                    # Upload file
                    result = self.upload_file(local_file_path, remote_file_path)
                    uploaded_files.append(result)
                    uploaded_count += 1

                    if progress_callback:
                        progress = (uploaded_count / total_files) * 100
                        progress_callback(progress, uploaded_count, total_files)

            logger.info(f"Successfully uploaded directory {local_dir} to {remote_dir}")
            return {
                "status": "completed",
                "local_dir": local_dir,
                "remote_dir": remote_dir,
                "uploaded_files": uploaded_files,
                "total_files": total_files
            }

        except Exception as e:
            logger.error(f"Failed to upload directory {local_dir}: {e}")
            raise

    def download_directory(
        self,
        remote_dir: str,
        local_dir: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Download entire directory recursively.

        Args:
            remote_dir: Remote directory path
            local_dir: Local directory path
            progress_callback: Callback function for progress updates

        Returns:
            Download directory result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            # Create local directory
            os.makedirs(local_dir, exist_ok=True)

            downloaded_files = []
            total_files = 0
            downloaded_count = 0

            # Get all files recursively
            def get_all_files(path: str) -> List[str]:
                files = []
                try:
                    items = self.list_files(path)
                    for item in items:
                        if item["type"] == "file":
                            files.append(item["path"])
                        elif item["type"] == "directory":
                            files.extend(get_all_files(item["path"]))
                except:
                    pass
                return files

            all_files = get_all_files(remote_dir)
            total_files = len(all_files)

            # Download files
            for remote_file in all_files:
                rel_path = os.path.relpath(remote_file, remote_dir)
                local_file = os.path.join(local_dir, rel_path)

                # Create subdirectories if needed
                local_subdir = os.path.dirname(local_file)
                os.makedirs(local_subdir, exist_ok=True)

                # Download file
                result = self.download_file(remote_file, local_file)
                downloaded_files.append(result)
                downloaded_count += 1

                if progress_callback:
                    progress = (downloaded_count / total_files) * 100
                    progress_callback(progress, downloaded_count, total_files)

            logger.info(f"Successfully downloaded directory {remote_dir} to {local_dir}")
            return {
                "status": "completed",
                "remote_dir": remote_dir,
                "local_dir": local_dir,
                "downloaded_files": downloaded_files,
                "total_files": total_files
            }

        except Exception as e:
            logger.error(f"Failed to download directory {remote_dir}: {e}")
            raise

    def test_connection(self) -> Dict[str, Any]:
        """
        Test FTP connection and return server capabilities.

        Returns:
            Connection test result information
        """
        if not self.connected or not self.ftp:
            raise ConnectionError("Not connected to FTP server")

        try:
            # Test basic commands
            welcome = self.ftp.getwelcome()
            current_dir = self.ftp.pwd()
            
            # Test passive/active mode
            passive_supported = True
            try:
                self.ftp.set_pasv(True)
                self.ftp.set_pasv(False)
            except:
                passive_supported = False

            # Test FTPS if applicable
            ftps_supported = False
            if isinstance(self.ftp, FTP_TLS):
                try:
                    self.ftp.prot_p()
                    ftps_supported = True
                except:
                    pass

            return {
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "welcome_message": welcome,
                "current_directory": current_dir,
                "passive_mode": self.passive_mode,
                "passive_supported": passive_supported,
                "ftps_supported": ftps_supported,
                "use_ftps": self.use_ftps
            }

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
