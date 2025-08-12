"""Commands module for MCP Empty Server."""

from ai_admin.commands.base import EmptyCommand
from ai_admin.commands.registry import command_registry

# Import all Docker commands
from ai_admin.commands.docker_hub_images_command import DockerHubImagesCommand
from ai_admin.commands.docker_hub_image_info_command import DockerHubImageInfoCommand
from ai_admin.commands.docker_images_compare_command import DockerImagesCompareCommand
from ai_admin.commands.docker_images_command import DockerImagesCommand
from ai_admin.commands.docker_build_command import DockerBuildCommand
from ai_admin.commands.docker_push_command import DockerPushCommand
from ai_admin.commands.docker_search_command import DockerSearchCommand
from ai_admin.commands.docker_search_cli_command import DockerSearchCLICommand
from ai_admin.commands.docker_tag_command import DockerTagCommand
from ai_admin.commands.docker_remove_command import DockerRemoveCommand
from ai_admin.commands.docker_login_command import DockerLoginCommand

# Import Vast.ai commands
from ai_admin.commands.vast_create_command import VastCreateCommand
from ai_admin.commands.vast_destroy_command import VastDestroyCommand
from ai_admin.commands.vast_instances_command import VastInstancesCommand
from ai_admin.commands.vast_search_command import VastSearchCommand

# Import Kubernetes commands
from ai_admin.commands.k8s_deployment_create_command import K8sDeploymentCreateCommand
from ai_admin.commands.k8s_pod_create_command import K8sPodCreateCommand
from ai_admin.commands.k8s_pod_delete_command import K8sPodDeleteCommand
from ai_admin.commands.k8s_pod_status_command import K8sPodStatusCommand
from ai_admin.commands.k8s_service_create_command import K8sServiceCreateCommand
from ai_admin.commands.k8s_logs_command import K8sLogsCommand, K8sExecCommand, K8sPortForwardCommand
from ai_admin.commands.k8s_namespace_command import K8sNamespaceCreateCommand, K8sNamespaceListCommand, K8sNamespaceDeleteCommand
from ai_admin.commands.k8s_configmap_command import K8sConfigMapCreateCommand, K8sSecretCreateCommand, K8sResourceDeleteCommand

# Import AI/LLM commands
from ai_admin.commands.llm_inference_command import LLMInferenceCommand
from ai_admin.commands.ollama_models_command import OllamaModelsCommand
from ai_admin.commands.ollama_run_command import OllamaRunCommand
from ai_admin.commands.ollama_status_command import OllamaStatusCommand
from ai_admin.commands.ollama_memory_command import OllamaMemoryCommand

# Import GitHub commands
from ai_admin.commands.github_create_repo_command import GitHubCreateRepoCommand
from ai_admin.commands.github_list_repos_command import GitHubListReposCommand

# Import Queue commands
from ai_admin.commands.queue_push_command import QueuePushCommand
from ai_admin.commands.queue_status_command import QueueStatusCommand
from ai_admin.commands.queue_cancel_command import QueueCancelCommand
from ai_admin.commands.queue_task_status_command import QueueTaskStatusCommand

# Import System commands
from ai_admin.commands.system_monitor_command import SystemMonitorCommand

# Import FTP commands
from ai_admin.commands.ftp_upload_command import FtpUploadCommand
from ai_admin.commands.ftp_download_command import FtpDownloadCommand
from ai_admin.commands.ftp_list_command import FtpListCommand
from ai_admin.commands.ftp_delete_command import FtpDeleteCommand

# Import Example command
from ai_admin.commands.example_command import ExampleCommand

# Import Test command
from ai_admin.commands.test_discovery_command import TestDiscoveryCommand

__all__ = [
    "EmptyCommand", 
    "command_registry",
    # Docker commands
    "DockerHubImagesCommand",
    "DockerHubImageInfoCommand", 
    "DockerImagesCompareCommand",
    "DockerImagesCommand",
    "DockerBuildCommand",
    "DockerPushCommand",
    "DockerSearchCommand",
    "DockerSearchCLICommand",
    "DockerTagCommand",
    "DockerRemoveCommand",
    "DockerLoginCommand",
    # Vast.ai commands
    "VastCreateCommand",
    "VastDestroyCommand",
    "VastInstancesCommand",
    "VastSearchCommand",
    # Kubernetes commands
    "K8sDeploymentCreateCommand",
    "K8sPodCreateCommand",
    "K8sPodDeleteCommand",
    "K8sPodStatusCommand",
    "K8sServiceCreateCommand",
    "K8sLogsCommand",
    "K8sExecCommand",
    "K8sNamespaceCreateCommand",
    "K8sNamespaceListCommand",
    "K8sNamespaceDeleteCommand",
    "K8sConfigMapCreateCommand",
    "K8sSecretCreateCommand",
    "K8sResourceDeleteCommand",
    "K8sPortForwardCommand",
    # AI/LLM commands
    "LLMInferenceCommand",
    "OllamaModelsCommand",
    "OllamaRunCommand",
    "OllamaStatusCommand",
    "OllamaMemoryCommand",
    # GitHub commands
    "GitHubCreateRepoCommand",
    "GitHubListReposCommand",
    # Queue commands
    "QueuePushCommand",
    "QueueStatusCommand",
    "QueueCancelCommand",
    "QueueTaskStatusCommand",
    # System commands
    "SystemMonitorCommand",
    # FTP commands
    "FtpUploadCommand",
    "FtpDownloadCommand", 
    "FtpListCommand",
    "FtpDeleteCommand",
    # Example command
    "ExampleCommand",
    # Test command
    "TestDiscoveryCommand"
] 