#!/usr/bin/env python3
"""Test script to check command imports."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing command imports...")
    
    # Test basic imports
    from ai_admin.commands.registry import command_registry
    print("✅ command_registry imported successfully")
    
    # Test Docker commands
    from ai_admin.commands.docker_images_command import DockerImagesCommand
    print("✅ DockerImagesCommand imported successfully")
    
    from ai_admin.commands.docker_build_command import DockerBuildCommand
    print("✅ DockerBuildCommand imported successfully")
    
    from ai_admin.commands.docker_push_command import DockerPushCommand
    print("✅ DockerPushCommand imported successfully")
    
    # Test Vast.ai commands
    from ai_admin.commands.vast_instances_command import VastInstancesCommand
    print("✅ VastInstancesCommand imported successfully")
    
    # Test Kubernetes commands
    from ai_admin.commands.k8s_logs_command import K8sLogsCommand, K8sExecCommand, K8sPortForwardCommand
    print("✅ K8sLogsCommand, K8sExecCommand, K8sPortForwardCommand imported successfully")
    
    from ai_admin.commands.k8s_configmap_command import K8sConfigmapCommand, K8sSecretCreateCommand, K8sResourceDeleteCommand
    print("✅ K8sConfigmapCommand, K8sSecretCreateCommand, K8sResourceDeleteCommand imported successfully")
    
    # Test AI/LLM commands
    from ai_admin.commands.ollama_status_command import OllamaStatusCommand
    print("✅ OllamaStatusCommand imported successfully")
    
    # Test GitHub commands
    from ai_admin.commands.github_list_repos_command import GithubListReposCommand
    print("✅ GithubListReposCommand imported successfully")
    
    # Test Queue commands
    from ai_admin.commands.queue_status_command import QueueStatusCommand
    print("✅ QueueStatusCommand imported successfully")
    
    # Test System commands
    from ai_admin.commands.system_monitor_command import SystemMonitorCommand
    print("✅ SystemMonitorCommand imported successfully")
    
    # Test Example command
    from ai_admin.commands.example_command import ExampleCommand
    print("✅ ExampleCommand imported successfully")
    
    print("\n🎉 All command imports successful!")
    
    # Test command discovery
    print("\nTesting command discovery...")
    command_registry.discover_commands("ai_admin.commands")
    all_commands = command_registry.get_all_commands()
    print(f"📊 Total commands discovered: {len(all_commands)}")
    
    if all_commands:
        print("📋 Discovered commands:")
        for cmd_name in sorted(all_commands.keys()):
            print(f"   • {cmd_name}")
    else:
        print("❌ No commands discovered!")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1) 