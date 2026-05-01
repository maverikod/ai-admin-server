#!/usr/bin/env python3
"""
Examples of using Docker image viewing commands in AI Admin Server.

This script demonstrates how to use the new Docker image commands
for viewing local and remote images, getting detailed information,
and comparing images.
"""

import asyncio
import json
from typing import Dict, Any


async def example_view_local_images():
    """Example: View local Docker images."""
    print("=== Example: View Local Docker Images ===")
    
    # Example 1: View all local images in JSON format
    command1 = {
        "method": "docker_images",
        "params": {
            "format_output": "json",
            "all_images": False
        }
    }
    
    # Example 2: View specific repository
    command2 = {
        "method": "docker_images",
        "params": {
            "repository": "nginx",
            "format_output": "json"
        }
    }
    
    # Example 3: View only image IDs (quiet mode)
    command3 = {
        "method": "docker_images",
        "params": {
            "quiet": True
        }
    }
    
    print("Command 1 - All local images:")
    print(json.dumps(command1, indent=2))
    print("\nCommand 2 - Specific repository:")
    print(json.dumps(command2, indent=2))
    print("\nCommand 3 - Quiet mode (only IDs):")
    print(json.dumps(command3, indent=2))
    print()


async def example_view_remote_images():
    """Example: View remote Docker Hub images."""
    print("=== Example: View Remote Docker Hub Images ===")
    
    # Example 1: Search for popular images
    command1 = {
        "method": "docker_hub_images",
        "params": {
            "query": "nginx",
            "limit": 5,
            "official_only": True,
            "sort_by": "stars",
            "order": "desc"
        }
    }
    
    # Example 2: Get user's repositories
    command2 = {
        "method": "docker_hub_images",
        "params": {
            "username": "library",
            "limit": 10,
            "sort_by": "pulls",
            "order": "desc"
        }
    }
    
    # Example 3: Search with tags included
    command3 = {
        "method": "docker_hub_images",
        "params": {
            "query": "python",
            "limit": 3,
            "include_tags": True,
            "official_only": True
        }
    }
    
    print("Command 1 - Search popular nginx images:")
    print(json.dumps(command1, indent=2))
    print("\nCommand 2 - Get official library images:")
    print(json.dumps(command2, indent=2))
    print("\nCommand 3 - Search Python images with tags:")
    print(json.dumps(command3, indent=2))
    print()


async def example_get_image_info():
    """Example: Get detailed image information."""
    print("=== Example: Get Detailed Image Information ===")
    
    # Example 1: Get info about official nginx image
    command1 = {
        "method": "docker_hub_image_info",
        "params": {
            "image_name": "library/nginx",
            "tag": "latest",
            "include_layers": True
        }
    }
    
    # Example 2: Get info about Ubuntu image
    command2 = {
        "method": "docker_hub_image_info",
        "params": {
            "image_name": "library/ubuntu",
            "tag": "20.04",
            "include_layers": False,
            "include_usage": True
        }
    }
    
    # Example 3: Get info about user's custom image
    command3 = {
        "method": "docker_hub_image_info",
        "params": {
            "image_name": "myuser/myapp",
            "tag": "v1.0.0"
        }
    }
    
    print("Command 1 - Nginx image info with layers:")
    print(json.dumps(command1, indent=2))
    print("\nCommand 2 - Ubuntu image info with usage:")
    print(json.dumps(command2, indent=2))
    print("\nCommand 3 - Custom user image info:")
    print(json.dumps(command3, indent=2))
    print()


async def example_compare_images():
    """Example: Compare local and remote images."""
    print("=== Example: Compare Local and Remote Images ===")
    
    # Example 1: Compare specific image
    command1 = {
        "method": "docker_images_compare",
        "params": {
            "image_name": "nginx",
            "check_updates": True,
            "include_dangling": False
        }
    }
    
    # Example 2: Compare all local images
    command2 = {
        "method": "docker_images_compare",
        "params": {
            "include_all_local": True,
            "check_updates": True,
            "include_dangling": False
        }
    }
    
    # Example 3: Compare with dangling images included
    command3 = {
        "method": "docker_images_compare",
        "params": {
            "include_all_local": True,
            "check_updates": False,
            "include_dangling": True
        }
    }
    
    print("Command 1 - Compare specific nginx image:")
    print(json.dumps(command1, indent=2))
    print("\nCommand 2 - Compare all local images:")
    print(json.dumps(command2, indent=2))
    print("\nCommand 3 - Compare with dangling images:")
    print(json.dumps(command3, indent=2))
    print()


async def example_workflow():
    """Example: Complete workflow for image management."""
    print("=== Example: Complete Image Management Workflow ===")
    
    workflow = [
        # Step 1: Check what local images we have
        {
            "step": 1,
            "description": "Check local images",
            "command": {
                "method": "docker_images",
                "params": {
                    "format_output": "json",
                    "all_images": False
                }
            }
        },
        
        # Step 2: Search for updates on Docker Hub
        {
            "step": 2,
            "description": "Search for nginx updates",
            "command": {
                "method": "docker_hub_images",
                "params": {
                    "query": "nginx",
                    "limit": 5,
                    "official_only": True,
                    "sort_by": "updated",
                    "order": "desc"
                }
            }
        },
        
        # Step 3: Get detailed info about latest nginx
        {
            "step": 3,
            "description": "Get detailed nginx info",
            "command": {
                "method": "docker_hub_image_info",
                "params": {
                    "image_name": "library/nginx",
                    "tag": "latest",
                    "include_layers": True
                }
            }
        },
        
        # Step 4: Compare local vs remote
        {
            "step": 4,
            "description": "Compare local and remote images",
            "command": {
                "method": "docker_images_compare",
                "params": {
                    "image_name": "nginx",
                    "check_updates": True
                }
            }
        }
    ]
    
    print("Complete workflow for image management:")
    for step in workflow:
        print(f"\nStep {step['step']}: {step['description']}")
        print(json.dumps(step['command'], indent=2))
    print()


def print_response_example():
    """Print example response structure."""
    print("=== Example Response Structure ===")
    
    example_response = {
        "status": "success",
        "data": {
            "status": "success",
            "query": "nginx",
            "total_count": 150,
            "results_count": 5,
            "results": [
                {
                    "name": "library/nginx",
                    "description": "Official nginx docker image",
                    "is_official": True,
                    "star_count": 15000,
                    "pull_count": 1000000,
                    "last_updated": "2024-01-01T12:00:00Z"
                }
            ],
            "search_params": {
                "limit": 5,
                "official_only": True,
                "sort_by": "stars",
                "order": "desc"
            },
            "timestamp": "2024-01-01T12:00:00.000Z",
            "execution_time_ms": 150.5
        }
    }
    
    print("Example success response:")
    print(json.dumps(example_response, indent=2))
    print()


async def main():
    """Run all examples."""
    print("Docker Images Commands Examples")
    print("=" * 50)
    print()
    
    await example_view_local_images()
    await example_view_remote_images()
    await example_get_image_info()
    await example_compare_images()
    await example_workflow()
    print_response_example()
    
    print("Examples completed!")
    print("\nTo use these commands:")
    print("1. Start the AI Admin Server")
    print("2. Send JSON-RPC requests with the command structures shown above")
    print("3. Handle the responses according to the example response structure")


if __name__ == "__main__":
    asyncio.run(main()) 