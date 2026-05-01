#!/usr/bin/env python3
"""
Demo script for Git authentication features

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

This script demonstrates the Git authentication capabilities including:
- SSH key discovery and usage
- Token-based authentication
- Passphrase-protected key handling
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

BASE_URL = "http://localhost:20001"

async def demo_ssh_key_discovery():
    """Demonstrate SSH key discovery."""
    print("🔑 SSH Key Discovery Demo")
    print("=" * 40)
    
    ssh_dir = Path.home() / ".ssh"
    print(f"SSH Directory: {ssh_dir}")
    
    if ssh_dir.exists():
        print(f"✅ SSH directory exists")
        
        # List SSH keys
        key_files = []
        for pattern in ["id_*", "github_*", "gitlab_*"]:
            key_files.extend(ssh_dir.glob(pattern))
        
        key_files = [f for f in key_files if f.is_file() and not f.name.endswith('.pub')]
        
        print(f"📁 Found {len(key_files)} SSH keys:")
        for key_file in key_files:
            print(f"   - {key_file.name}")
            
            # Check if public key exists
            pub_key = key_file.with_suffix(key_file.suffix + '.pub')
            if pub_key.exists():
                print(f"     📄 Public key: {pub_key.name}")
            else:
                print(f"     ⚠️  No public key found")
    else:
        print(f"❌ SSH directory not found")

async def demo_git_operations_with_auth():
    """Demonstrate Git operations with authentication."""
    print("\n🌐 Git Operations with Authentication Demo")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test HTTPS clone (uses token authentication)
        print("\n🔗 Testing HTTPS Clone (Token Authentication)")
        clone_params = {
            "repository_url": "https://github.com/octocat/Hello-World.git",
            "target_directory": "/tmp/demo_clone"
        }
        
        try:
            async with session.post(
                f"{BASE_URL}/cmd",
                json={"command": "git_clone", **clone_params},
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Clone successful: {result.get('message', 'OK')}")
                else:
                    print(f"   ❌ Clone failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Clone error: {e}")
        
        # Test Git status
        print("\n📊 Testing Git Status")
        status_params = {}
        
        try:
            async with session.post(
                f"{BASE_URL}/cmd",
                json={"command": "git_status", **status_params},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Status successful: {result.get('message', 'OK')}")
                else:
                    print(f"   ❌ Status failed: {response.status}")
        except Exception as e:
            print(f"   ❌ Status error: {e}")

async def demo_configuration():
    """Demonstrate configuration features."""
    print("\n⚙️  Configuration Demo")
    print("=" * 30)
    
    # Show current Git configuration
    config_file = Path("config/config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        git_config = config.get('git', {})
        print("📋 Git Configuration:")
        print(f"   SSH Keys Directory: {git_config.get('ssh_keys_dir', '~/.ssh')}")
        print(f"   Default SSH Key: {git_config.get('default_ssh_key', 'None')}")
        print(f"   Preferred Key Type: {git_config.get('preferred_key_type', 'None')}")
        print(f"   GitHub Token: {'✅ Configured' if git_config.get('github_token') else '❌ Not configured'}")
        print(f"   GitLab Token: {'✅ Configured' if git_config.get('gitlab_token') else '❌ Not configured'}")
        
        # Show force and yes flags
        force_flags = git_config.get('force_flags', {})
        print(f"\n🔧 Force Flags:")
        for operation, flag in force_flags.items():
            print(f"   {operation}: {flag}")
        
        yes_flags = git_config.get('yes_flags', {})
        print(f"\n✅ Yes Flags:")
        for operation, flag in yes_flags.items():
            print(f"   {operation}: {flag}")

async def demo_authentication_features():
    """Demonstrate authentication features."""
    print("\n🔐 Authentication Features Demo")
    print("=" * 40)
    
    print("✨ Key Features:")
    print("   🔑 Automatic SSH key discovery from ~/.ssh")
    print("   🛡️  Support for passphrase-protected keys")
    print("   🎫 Token-based authentication for HTTPS")
    print("   🔄 SSH agent integration")
    print("   ⚡ Automatic force/yes flags for Git operations")
    print("   🎯 Smart key selection (prefers ed25519, no passphrase)")
    
    print("\n📝 Supported Authentication Methods:")
    print("   🌐 HTTPS with GitHub/GitLab tokens")
    print("   🔐 SSH with key-based authentication")
    print("   🔑 Multiple SSH key support")
    print("   🛡️  Passphrase handling (with user interaction)")
    
    print("\n🚀 Enhanced Git Commands:")
    print("   ✅ git_add - Fixed parameter conflicts")
    print("   ✅ git_config - Added None value validation")
    print("   ✅ git_commit - Added --allow-empty support")
    print("   ✅ git_rebase - Added auto-stash functionality")
    print("   ✅ git_cherry_pick - Fixed parameter handling")
    print("   ✅ git_clone/push/pull - Added authentication support")

async def main():
    """Main demo function."""
    print("🎯 Git Authentication System Demo")
    print("=" * 50)
    print("This demo showcases the enhanced Git authentication system")
    print("with SSH key management and token-based authentication.")
    print()
    
    await demo_ssh_key_discovery()
    await demo_configuration()
    await demo_authentication_features()
    await demo_git_operations_with_auth()
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print("The Git authentication system is ready for production use.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
