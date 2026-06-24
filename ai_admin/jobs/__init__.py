"""Job classes for queuemgr-based task execution.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from .docker_job import DockerJob
from .git_job import GitJob
from .github_job import GitHubJob
from .k8s_job import K8sJob
from .vast_job import VastJob
from .ftp_job import FtpJob
from .ollama_job import OllamaJob
from .ssl_job import SslJob
from .system_job import SystemJob

__all__ = [
    "DockerJob",
    "GitJob",
    "GitHubJob",
    "K8sJob",
    "VastJob",
    "FtpJob",
    "OllamaJob",
    "SslJob",
    "SystemJob",
]
