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
from ai_admin.commands.docker_pull_command import DockerPullCommand
from ai_admin.commands.docker_search_command import DockerSearchCommand
from ai_admin.commands.docker_search_cli_command import DockerSearchCLICommand
from ai_admin.commands.docker_network_ls_command import DockerNetworkLsCommand
from ai_admin.commands.docker_network_inspect_command import DockerNetworkInspectCommand
from ai_admin.commands.docker_network_create_command import DockerNetworkCreateCommand
from ai_admin.commands.docker_network_connect_command import DockerNetworkConnectCommand
from ai_admin.commands.docker_network_disconnect_command import DockerNetworkDisconnectCommand
from ai_admin.commands.docker_network_rm_command import DockerNetworkRmCommand
from ai_admin.commands.docker_tag_command import DockerTagCommand
from ai_admin.commands.docker_remove_command import DockerRemoveCommand
from ai_admin.commands.docker_run_command import DockerRunCommand
from ai_admin.commands.docker_start_command import DockerStartCommand
from ai_admin.commands.docker_stop_command import DockerStopCommand
from ai_admin.commands.docker_rm_command import DockerRmCommand
from ai_admin.commands.docker_cp_command import DockerCpCommand
from ai_admin.commands.docker_volume_command import DockerVolumeCommand
from ai_admin.commands.docker_restart_command import DockerRestartCommand
from ai_admin.commands.argocd_init_command import ArgoCDInitCommand
from ai_admin.commands.docker_logs_command import DockerLogsCommand
from ai_admin.commands.docker_containers_command import DockerContainersCommand
from ai_admin.commands.docker_exec_command import DockerExecCommand
from ai_admin.commands.docker_inspect_command import DockerInspectCommand
from ai_admin.commands.ollama_show_command import OllamaShowCommand
from ai_admin.commands.ollama_remove_command import OllamaRemoveCommand
from ai_admin.commands.ollama_copy_command import OllamaCopyCommand
from ai_admin.commands.ollama_push_command import OllamaPushCommand
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

# Import Kind commands
from ai_admin.commands.kind_cluster_command import KindClusterCommand
from ai_admin.commands.k8s_cluster_manager_command import K8sClusterManagerCommand

# Import SSL certificate commands
from ai_admin.commands.ssl_cert_generate_command import SSLCertGenerateCommand
from ai_admin.commands.ssl_cert_view_command import SSLCertViewCommand
from ai_admin.commands.ssl_cert_verify_command import SSLCertVerifyCommand
from ai_admin.commands.ssl_crl_command import SSLCrlCommand

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



# Import Test command
from ai_admin.commands.test_discovery_command import TestDiscoveryCommand

# Import Git commands
from ai_admin.commands.git_add_command import GitAddCommand
from ai_admin.commands.git_branch_command import GitBranchCommand
from ai_admin.commands.git_checkout_command import GitCheckoutCommand
from ai_admin.commands.git_clone_command import GitCloneCommand
from ai_admin.commands.git_commit_command import GitCommitCommand
from ai_admin.commands.git_diff_command import GitDiffCommand
from ai_admin.commands.git_init_command import GitInitCommand
from ai_admin.commands.git_pull_command import GitPullCommand
from ai_admin.commands.git_push_command import GitPushCommand
from ai_admin.commands.git_rebase_command import GitRebaseCommand
from ai_admin.commands.git_remote_command import GitRemoteCommand
from ai_admin.commands.git_reset_command import GitResetCommand
from ai_admin.commands.git_status_command import GitStatusCommand
from ai_admin.commands.git_fetch_command import GitFetchCommand
from ai_admin.commands.git_merge_command import GitMergeCommand
from ai_admin.commands.git_log_command import GitLogCommand
from ai_admin.commands.git_show_command import GitShowCommand
from ai_admin.commands.git_tag_command import GitTagCommand
from ai_admin.commands.git_stash_command import GitStashCommand
from ai_admin.commands.git_clean_command import GitCleanCommand
from ai_admin.commands.git_config_command import GitConfigCommand
from ai_admin.commands.git_grep_command import GitGrepCommand
from ai_admin.commands.git_blame_command import GitBlameCommand
from ai_admin.commands.git_cherry_pick_command import GitCherryPickCommand

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
    "DockerPullCommand",
    "DockerSearchCommand",
    "DockerSearchCLICommand",
    "DockerNetworkLsCommand",
    "DockerNetworkInspectCommand",
    "DockerNetworkCreateCommand",
    "DockerNetworkConnectCommand",
    "DockerNetworkDisconnectCommand",
    "DockerNetworkRmCommand",
    "DockerTagCommand",
    "DockerRemoveCommand",
    "DockerRunCommand",
    "DockerStartCommand",
    "DockerStopCommand",
    "DockerRmCommand",
    "DockerVolumeCommand",
    "DockerRestartCommand",
    "DockerLogsCommand",
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
    # Kind commands
    "KindClusterCommand",
    # Cluster Manager commands
    "K8sClusterManagerCommand",
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
    "TestDiscoveryCommand",
    # Git commands
    "GitAddCommand",
    "GitBranchCommand", 
    "GitCheckoutCommand",
    "GitCloneCommand",
    "GitCommitCommand",
    "GitDiffCommand",
    "GitInitCommand",
    "GitPullCommand",
    "GitPushCommand",
    "GitRebaseCommand",
    "GitRemoteCommand",
    "GitResetCommand",
    "GitStatusCommand",
    "GitFetchCommand",
    "GitMergeCommand",
    "GitLogCommand",
    "GitShowCommand",
    "GitTagCommand",
    "GitStashCommand",
    "GitCleanCommand",
    "GitConfigCommand",
    "GitGrepCommand",
    "GitBlameCommand",
    "GitCherryPickCommand"
] 