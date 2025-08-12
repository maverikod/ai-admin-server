"""AI Admin MCP Server with enhanced integration."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter import create_app
from mcp_proxy_adapter.core.logging import setup_logging, get_logger
from mcp_proxy_adapter.core.settings import (
    Settings, 
    get_server_host, 
    get_server_port, 
    get_server_debug,
    get_setting
)
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.commands.hooks import register_custom_commands_hook

# Import AI Admin specific components
from ai_admin.settings_manager import AIAdminSettingsManager, get_settings_manager
from ai_admin.hooks import register_ai_admin_hooks


def initialize_commands():
    """
    Initialize commands using the unified system initialization logic.
    This function is used both at startup and during reload.
    
    Returns:
        Number of commands discovered.
    """
    # Use the unified reload method from registry
    result = registry.reload_system()
    return result["total_commands"]


def custom_commands_hook(registry):
    """Hook function for registering AI Admin custom commands."""
    logger = get_logger("ai_admin")
    logger.info("Registering AI Admin custom commands via hook...")
    
    # Import all AI Admin commands
    from ai_admin.commands.system_monitor_command import SystemMonitorCommand
    from ai_admin.commands.docker_build_command import DockerBuildCommand
    from ai_admin.commands.docker_push_command import DockerPushCommand
    from ai_admin.commands.docker_images_command import DockerImagesCommand
    from ai_admin.commands.docker_search_command import DockerSearchCommand
    from ai_admin.commands.docker_pull_command import DockerPullCommand
    from ai_admin.commands.vast_search_command import VastSearchCommand
    from ai_admin.commands.vast_create_command import VastCreateCommand
    from ai_admin.commands.vast_destroy_command import VastDestroyCommand
    from ai_admin.commands.vast_instances_command import VastInstancesCommand
    from ai_admin.commands.ftp_upload_command import FtpUploadCommand
    from ai_admin.commands.ftp_download_command import FtpDownloadCommand
    from ai_admin.commands.ftp_list_command import FtpListCommand
    from ai_admin.commands.ftp_delete_command import FtpDeleteCommand
    from ai_admin.commands.queue_push_command import QueuePushCommand
    from ai_admin.commands.queue_status_command import QueueStatusCommand
    from ai_admin.commands.queue_cancel_command import QueueCancelCommand
    from ai_admin.commands.queue_task_status_command import QueueTaskStatusCommand
    from ai_admin.commands.github_list_repos_command import GitHubListReposCommand
    from ai_admin.commands.github_create_repo_command import GitHubCreateRepoCommand
    from ai_admin.commands.git_clone_command import GitCloneCommand
    from ai_admin.commands.git_status_command import GitStatusCommand
    from ai_admin.commands.git_add_command import GitAddCommand
    from ai_admin.commands.git_commit_command import GitCommitCommand
    from ai_admin.commands.git_push_command import GitPushCommand
    from ai_admin.commands.git_pull_command import GitPullCommand
    from ai_admin.commands.git_branch_command import GitBranchCommand
    from ai_admin.commands.git_checkout_command import GitCheckoutCommand
    from ai_admin.commands.git_init_command import GitInitCommand
    from ai_admin.commands.git_remote_command import GitRemoteCommand
    from ai_admin.commands.git_reset_command import GitResetCommand
    from ai_admin.commands.git_rebase_command import GitRebaseCommand
    from ai_admin.commands.git_diff_command import GitDiffCommand
    from ai_admin.commands.k8s_pod_status_command import K8sPodStatusCommand
    from ai_admin.commands.k8s_deployment_create_command import K8sDeploymentCreateCommand
    from ai_admin.commands.ollama_status_command import OllamaStatusCommand
    from ai_admin.commands.ollama_models_command import OllamaModelsCommand
    from ai_admin.commands.test_discovery_command import TestDiscoveryCommand
    
    # Register AI Admin commands
    commands_to_register = [
        SystemMonitorCommand,
        DockerBuildCommand,
        DockerPushCommand,
        DockerImagesCommand,
        DockerSearchCommand,
        DockerPullCommand,
        VastSearchCommand,
        VastCreateCommand,
        VastDestroyCommand,
        VastInstancesCommand,
        FtpUploadCommand,
        FtpDownloadCommand,
        FtpListCommand,
        FtpDeleteCommand,
        QueuePushCommand,
        QueueStatusCommand,
        QueueCancelCommand,
        QueueTaskStatusCommand,
        GitHubListReposCommand,
        GitHubCreateRepoCommand,
        GitCloneCommand,
        GitStatusCommand,
        GitAddCommand,
        GitCommitCommand,
        GitPushCommand,
        GitPullCommand,
        GitBranchCommand,
        GitCheckoutCommand,
        GitInitCommand,
        GitRemoteCommand,
        GitResetCommand,
        GitRebaseCommand,
        GitDiffCommand,
        K8sPodStatusCommand,
        K8sDeploymentCreateCommand,
        OllamaStatusCommand,
        OllamaModelsCommand,
        TestDiscoveryCommand
    ]
    
    for command_class in commands_to_register:
        if not registry.command_exists(command_class.name):
            registry.register_custom(command_class)
            logger.info(f"Registered: {command_class.name} command")
        else:
            logger.debug(f"Command '{command_class.name}' is already registered, skipping")
    
    logger.info(f"Total AI Admin commands registered: {len(commands_to_register)}")


def setup_hooks():
    """Setup hooks for AI Admin server."""
    logger = get_logger("ai_admin")
    logger.info("Setting up AI Admin hooks...")
    
    # Register custom commands hook
    register_custom_commands_hook(custom_commands_hook)
    
    # Register AI Admin specific hooks
    from mcp_proxy_adapter.commands.hooks import hooks
    register_ai_admin_hooks(hooks)
    
    logger.info("Registered: AI Admin hooks")


def main():
    """Run the AI Admin server."""
    # Load configuration from config.json in the same directory
    config_path = "config/config.json"
    if os.path.exists(config_path):
        from mcp_proxy_adapter.config import config
        config.load_from_file(config_path)
        print(f"✅ Loaded configuration from: {config_path}")
    else:
        print(f"⚠️  Configuration file not found: {config_path}")
        print("   Using default configuration")
        from mcp_proxy_adapter.config import config
        config.load_config()
    
    # Setup logging with configuration
    setup_logging()
    logger = get_logger("ai_admin")
    
    # Initialize custom settings manager
    settings_manager = get_settings_manager()
    
    # Print custom settings summary
    settings_manager.print_settings_summary()
    
    # Get settings from configuration
    server_settings = Settings.get_server_settings()
    logging_settings = Settings.get_logging_settings()
    commands_settings = Settings.get_commands_settings()
    
    # Print server header and description
    print("=" * 80)
    print("🚀 AI ADMIN - ENHANCED MCP SERVER")
    print("=" * 80)
    print("📋 Description: AI Admin server with command autodiscovery support to manage DockerHub, GitHub, Vast.ai GPU instances, and Kubernetes resources")
    print("🔧 Version: 1.0.0")
    print("⚙️  Configuration:")
    print(f"   • Server: {server_settings['host']}:{server_settings['port']}")
    print(f"   • Debug: {server_settings['debug']}")
    print(f"   • Log Level: {logging_settings['level']}")
    print(f"   • Log Directory: {logging_settings['log_dir']}")
    print(f"   • Auto Discovery: {commands_settings['auto_discovery']}")
    print("🔧 Available Commands:")
    print("   • Built-in: 8")
    print("   • Custom: 0")
    print("   • Auto-discovered: 0")
    print("   📁 Config: config, reload, settings, load, unload, plugins")
    print("🎯 Enhanced Features:")
    print("   • Advanced JSON-RPC API")
    print("   • Automatic command discovery")
    print("   • Hooks system for extensibility")
    print("   • Built-in logging and error handling")
    print("   • OpenAPI schema generation")
    print("   • Configuration-driven settings")
    print("   • Custom settings management")
    print("   • Performance monitoring")
    print("   • Security monitoring")
    print("   • Operation-specific hooks (Docker, Vast.ai, FTP, Queue)")
    print("   • Credential management")
    print("   • Settings validation")
    print("=" * 80)
    
    # Validate settings
    validation_result = settings_manager.validate_settings()
    if not validation_result["valid"]:
        logger.warning(f"Configuration validation warnings: {validation_result['warnings']}")
    
    logger.info("Starting AI Admin MCP Proxy Adapter Server...")
    logger.info(f"Server configuration: {server_settings}")
    logger.info(f"Logging configuration: {logging_settings}")
    logger.info(f"Commands configuration: {commands_settings}")
    
    # Setup hooks for command processing
    setup_hooks()
    
    # Initialize commands
    initialize_commands()
    
    # Create application with settings from configuration
    app = create_app(
        title="AI Admin - Enhanced MCP Server",
        description="AI Admin server with command autodiscovery support to manage DockerHub, GitHub, Vast.ai GPU instances, and Kubernetes resources",
        version="2.0.0"
    )
    
    # Run the server with configuration settings
    import uvicorn
    uvicorn.run(
        app,
        host=server_settings['host'],
        port=server_settings['port'],
        log_level=server_settings['log_level'].lower()
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Admin MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        os.environ["DEBUG"] = "true"
    
    main() 