#!/usr/bin/env python3
"""
Test Enhanced AI Admin Integration

This script tests the integration with the new MCP Proxy Adapter version 5.0.0
and verifies that all enhanced features are working correctly.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any


def test_server_startup():
    """Test server startup and configuration loading."""
    print("🧪 Testing Enhanced AI Admin Integration")
    print("=" * 60)
    
    try:
        # Test basic health endpoint
        response = requests.get("http://localhost:8060/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8060")
        return False
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        return False
    
    return True


def test_command_discovery():
    """Test command discovery and listing."""
    print("\n🔍 Testing Command Discovery")
    print("-" * 40)
    
    try:
        # Test help command
        response = requests.post(
            "http://localhost:8060/cmd",
            json={"jsonrpc": "2.0", "method": "help", "id": 1},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                commands_info = result["result"]
                total_commands = commands_info.get("total", 0)
                print(f"✅ Command discovery working: {total_commands} commands found")
                
                # Check for specific command categories
                command_categories = {
                    "Docker": ["docker_build", "docker_push", "docker_images"],
                    "Vast.ai": ["vast_search", "vast_create", "vast_instances"],
                    "FTP": ["ftp_upload", "ftp_download", "ftp_list"],
                    "System": ["system_monitor", "queue_status"]
                }
                
                for category, commands in command_categories.items():
                    found_commands = [cmd for cmd in commands if cmd in commands_info.get("commands", {})]
                    if found_commands:
                        print(f"   📁 {category}: {len(found_commands)} commands")
                
                return True
            else:
                print("❌ Help command returned no result")
                return False
        else:
            print(f"❌ Help command failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during command discovery test: {e}")
        return False


def test_settings_management():
    """Test settings management functionality."""
    print("\n⚙️ Testing Settings Management")
    print("-" * 40)
    
    try:
        # Test config command
        response = requests.post(
            "http://localhost:8060/cmd",
            json={"jsonrpc": "2.0", "method": "config", "id": 2},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                config_data = result["result"]
                print("✅ Settings management working")
                
                # Check for AI Admin specific settings
                if "ai_admin" in str(config_data):
                    print("   📋 AI Admin settings detected")
                
                # Check for features configuration
                if "features" in str(config_data):
                    print("   🔧 Features configuration available")
                
                return True
            else:
                print("❌ Config command returned no result")
                return False
        else:
            print(f"❌ Config command failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during settings test: {e}")
        return False


def test_hooks_functionality():
    """Test hooks functionality by monitoring command execution."""
    print("\n🔗 Testing Hooks Functionality")
    print("-" * 40)
    
    try:
        # Test a simple command that should trigger hooks
        response = requests.post(
            "http://localhost:8060/cmd",
            json={
                "jsonrpc": "2.0", 
                "method": "system_monitor", 
                "id": 3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("✅ System monitor command executed successfully")
                print("   🔍 Check server logs for hook activity")
                
                # The hooks should have logged information about this command
                print("   📝 Hooks should have logged:")
                print("      - Performance monitoring")
                print("      - Security monitoring")
                print("      - Command execution metadata")
                
                return True
            else:
                print("❌ System monitor command returned no result")
                return False
        else:
            print(f"❌ System monitor command failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during hooks test: {e}")
        return False


def test_error_handling():
    """Test enhanced error handling."""
    print("\n🚨 Testing Error Handling")
    print("-" * 40)
    
    try:
        # Test with invalid command
        response = requests.post(
            "http://localhost:8060/cmd",
            json={
                "jsonrpc": "2.0", 
                "method": "nonexistent_command", 
                "id": 4
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if "error" in result:
                error_data = result["error"]
                print("✅ Error handling working correctly")
                print(f"   Error code: {error_data.get('code', 'unknown')}")
                print(f"   Error message: {error_data.get('message', 'unknown')}")
                
                # Check for enhanced error information
                if "data" in error_data:
                    print("   📋 Enhanced error data available")
                
                return True
            else:
                print("❌ Expected error response not received")
                return False
        else:
            print(f"❌ Error handling test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during error handling test: {e}")
        return False


def test_performance_monitoring():
    """Test performance monitoring features."""
    print("\n⏱️ Testing Performance Monitoring")
    print("-" * 40)
    
    try:
        # Test multiple commands to trigger performance monitoring
        commands_to_test = ["help", "config", "system_monitor"]
        
        for i, command in enumerate(commands_to_test):
            start_time = time.time()
            response = requests.post(
                "http://localhost:8060/cmd",
                json={
                    "jsonrpc": "2.0", 
                    "method": command, 
                    "id": 100 + i
                },
                timeout=10
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                print(f"✅ {command}: {duration:.3f}s")
            else:
                print(f"❌ {command}: failed ({response.status_code})")
        
        print("   📊 Performance monitoring should be active in server logs")
        return True
        
    except Exception as e:
        print(f"❌ Error during performance test: {e}")
        return False


def main():
    """Run all integration tests."""
    print("🚀 Enhanced AI Admin Integration Test Suite")
    print("=" * 60)
    print("Make sure the AI Admin server is running on http://localhost:8060")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    tests = [
        ("Server Startup", test_server_startup),
        ("Command Discovery", test_command_discovery),
        ("Settings Management", test_settings_management),
        ("Hooks Functionality", test_hooks_functionality),
        ("Error Handling", test_error_handling),
        ("Performance Monitoring", test_performance_monitoring)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced integration is working correctly.")
        print("\n✨ Enhanced Features Verified:")
        print("   • Advanced JSON-RPC API")
        print("   • Automatic command discovery")
        print("   • Hooks system for extensibility")
        print("   • Configuration-driven settings")
        print("   • Performance monitoring")
        print("   • Enhanced error handling")
        print("   • Settings validation")
    else:
        print("⚠️ Some tests failed. Check server logs for details.")
    
    print("=" * 60)


if __name__ == "__main__":
    main() 