#!/usr/bin/env python3
"""Script to fix missing SuccessResult imports in command files."""

import os
import re
from pathlib import Path

def fix_success_result_imports(file_path):
    """Fix missing SuccessResult imports in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if SuccessResult is used but not imported
        if 'SuccessResult(' in content and 'SuccessResult' not in content.split('\n')[0:20]:
            # Find existing import line for mcp_proxy_adapter.commands.result
            lines = content.split('\n')
            insert_index = 0
            
            # Look for existing import from mcp_proxy_adapter.commands.result
            for i, line in enumerate(lines):
                if 'from mcp_proxy_adapter.commands.result import' in line:
                    # Add SuccessResult to existing import
                    if 'SuccessResult' not in line:
                        lines[i] = line.replace(
                            'from mcp_proxy_adapter.commands.result import',
                            'from mcp_proxy_adapter.commands.result import SuccessResult,'
                        ).replace(',,', ',')
                    insert_index = -1  # Don't add new import
                    break
                elif line.startswith('from mcp_proxy_adapter.commands.result import'):
                    # Add SuccessResult to existing import
                    if 'SuccessResult' not in line:
                        lines[i] = line.replace(
                            'from mcp_proxy_adapter.commands.result import',
                            'from mcp_proxy_adapter.commands.result import SuccessResult,'
                        ).replace(',,', ',')
                    insert_index = -1  # Don't add new import
                    break
            
            # If no existing import found, add new one
            if insert_index != -1:
                # Find the right place to add imports (after docstring)
                in_docstring = False
                for i, line in enumerate(lines):
                    if line.strip().startswith('"""') and not in_docstring:
                        in_docstring = True
                    elif line.strip().endswith('"""') and in_docstring:
                        insert_index = i + 1
                        break
                    elif not in_docstring and line.strip() and not line.strip().startswith('#'):
                        insert_index = i
                        break
                
                # Insert import
                lines.insert(insert_index, 'from mcp_proxy_adapter.commands.result import SuccessResult')
            
            content = '\n'.join(lines)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed SuccessResult import in {file_path}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all command files."""
    commands_dir = Path("ai_admin/commands")
    
    if not commands_dir.exists():
        print("Commands directory not found!")
        return
    
    fixed_count = 0
    
    # List of files that need SuccessResult import
    files_to_fix = [
        "docker_hub_images_command.py",
        "docker_images_command.py", 
        "docker_images_compare_command.py",
        "docker_login_command.py",
        "docker_network_ls_command.py",
        "example_di_command.py",
        "example_unified_security_command.py",
        "ftp_list_command.py",
        "k8s_cluster_command.py",
        "k8s_cluster_setup_command.py",
        "k8s_configmap_command.py",
        "k8s_deployment_create_command.py",
        "k8s_logs_command.py",
        "k8s_mtls_setup_command.py",
        "k8s_namespace_command.py",
        "k8s_pod_create_command.py",
        "k8s_pod_delete_command.py",
        "k8s_pod_status_command.py",
        "k8s_service_create_command.py",
        "kind_cluster_command.py",
        "llm_inference_command.py",
        "mtls_roles_command.py",
        "ollama_copy_command.py",
        "ollama_memory_command.py",
        "ollama_models_command.py",
        "ollama_push_command.py",
        "ollama_remove_command.py",
        "ollama_run_command.py",
        "ollama_show_command.py",
        "ollama_status_command.py",
        "queue_cancel_command.py",
        "queue_manage_command.py",
        "queue_push_command.py",
        "queue_ssl_command.py",
        "queue_status_command.py",
        "queue_task_status_command.py",
        "security_command.py"
    ]
    
    for file_name in files_to_fix:
        file_path = commands_dir / file_name
        if file_path.exists():
            if fix_success_result_imports(file_path):
                fixed_count += 1
    
    print(f"Fixed SuccessResult imports in {fixed_count} files")

if __name__ == "__main__":
    main()
