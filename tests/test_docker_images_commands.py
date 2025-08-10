#!/usr/bin/env python3
"""
Tests for Docker image viewing commands.

This module contains unit tests for the new Docker image commands:
- docker_hub_images
- docker_hub_image_info  
- docker_images_compare
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from ai_admin.commands.docker_hub_images_command import DockerHubImagesCommand
from ai_admin.commands.docker_hub_image_info_command import DockerHubImageInfoCommand
from ai_admin.commands.docker_images_compare_command import DockerImagesCompareCommand
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult


class TestDockerHubImagesCommand:
    """Test cases for DockerHubImagesCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DockerHubImagesCommand()
    
    @pytest.mark.asyncio
    async def test_execute_search_query(self, command):
        """Test executing search query."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "count": 1,
                "results": [{
                    "repo_name": "library/nginx",
                    "name": "nginx",
                    "short_description": "Official nginx image",
                    "is_official": True,
                    "star_count": 15000,
                    "pull_count": 1000000,
                    "last_updated": "2024-01-01T12:00:00Z"
                }]
            }
            mock_response.url = "https://hub.docker.com/v2/search/repositories/"
            mock_get.return_value = mock_response
            
            result = await command.execute(query="nginx", limit=5)
            
            assert isinstance(result, SuccessResult)
            assert result.data["status"] == "success"
            assert result.data["query"] == "nginx"
            assert result.data["results_count"] == 1
            assert len(result.data["results"]) == 1
            assert result.data["results"][0]["name"] == "library/nginx"
    
    @pytest.mark.asyncio
    async def test_execute_with_username(self, command):
        """Test executing with username parameter."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "count": 2,
                "results": [
                    {"repo_name": "library/nginx", "name": "nginx"},
                    {"repo_name": "library/ubuntu", "name": "ubuntu"}
                ]
            }
            mock_response.url = "https://hub.docker.com/v2/repositories/library/"
            mock_get.return_value = mock_response
            
            result = await command.execute(username="library", limit=10)
            
            assert isinstance(result, SuccessResult)
            assert result.data["username"] == "library"
            assert result.data["results_count"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_api_error(self, command):
        """Test handling API errors."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.url = "https://hub.docker.com/v2/search/repositories/"
            mock_get.return_value = mock_response
            
            result = await command.execute(query="nonexistent")
            
            assert isinstance(result, ErrorResult)
            assert result.code == "HUB_IMAGES_ERROR"
            assert "404" in result.message
    
    @pytest.mark.asyncio
    async def test_execute_network_error(self, command):
        """Test handling network errors."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = await command.execute(query="nginx")
            
            assert isinstance(result, ErrorResult)
            assert result.code == "INTERNAL_ERROR"
    
    def test_get_schema(self, command):
        """Test schema generation."""
        schema = command.get_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]
        assert "official_only" in schema["properties"]


class TestDockerHubImageInfoCommand:
    """Test cases for DockerHubImageInfoCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DockerHubImageInfoCommand()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, command):
        """Test successful execution."""
        with patch('requests.get') as mock_get:
            # Mock repository info response
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {
                "name": "nginx",
                "full_name": "library/nginx",
                "description": "Official nginx image",
                "is_official": True,
                "star_count": 15000,
                "pull_count": 1000000,
                "last_updated": "2024-01-01T12:00:00Z"
            }
            
            # Mock tag info response
            tag_response = Mock()
            tag_response.status_code = 200
            tag_response.json.return_value = {
                "name": "latest",
                "full_size": 133700000,
                "images": [{
                    "architecture": "amd64",
                    "os": "linux",
                    "size": 133700000
                }]
            }
            
            mock_get.side_effect = [repo_response, tag_response]
            
            result = await command.execute(
                image_name="library/nginx",
                tag="latest",
                include_layers=True
            )
            
            assert isinstance(result, SuccessResult)
            assert result.data["image_name"] == "library/nginx"
            assert result.data["tag"] == "latest"
            assert result.data["repository"]["name"] == "nginx"
            assert result.data["tag_info"]["name"] == "latest"
    
    @pytest.mark.asyncio
    async def test_execute_normalize_image_name(self, command):
        """Test image name normalization."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "name": "nginx",
                "full_name": "library/nginx"
            }
            mock_get.return_value = mock_response
            
            result = await command.execute(image_name="nginx")
            
            assert isinstance(result, SuccessResult)
            assert result.data["image_name"] == "library/nginx"
    
    @pytest.mark.asyncio
    async def test_execute_missing_image_name(self, command):
        """Test error handling for missing image name."""
        result = await command.execute(image_name="")
        
        assert isinstance(result, ErrorResult)
        assert result.code == "HUB_IMAGE_INFO_ERROR"
        assert "required" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_execute_tag_not_found(self, command):
        """Test handling tag not found."""
        with patch('requests.get') as mock_get:
            # Repository exists but tag doesn't
            repo_response = Mock()
            repo_response.status_code = 200
            repo_response.json.return_value = {"name": "nginx"}
            
            tag_response = Mock()
            tag_response.status_code = 404
            
            mock_get.side_effect = [repo_response, tag_response]
            
            result = await command.execute(
                image_name="library/nginx",
                tag="nonexistent"
            )
            
            assert isinstance(result, SuccessResult)
            assert result.data["tag_info"] is None
    
    def test_get_schema(self, command):
        """Test schema generation."""
        schema = command.get_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "image_name" in schema["properties"]
        assert "tag" in schema["properties"]
        assert "required" in schema
        assert "image_name" in schema["required"]


class TestDockerImagesCompareCommand:
    """Test cases for DockerImagesCompareCommand."""
    
    @pytest.fixture
    def command(self):
        """Create command instance."""
        return DockerImagesCompareCommand()
    
    @pytest.mark.asyncio
    async def test_execute_compare_specific_image(self, command):
        """Test comparing specific image."""
        with patch.object(command, '_get_local_images') as mock_local, \
             patch.object(command, '_get_remote_image_info') as mock_remote:
            
            mock_local.return_value = [{
                "Repository": "nginx",
                "Tag": "latest",
                "CreatedAt": "2024-01-01T10:00:00Z",
                "Size": "133MB"
            }]
            
            mock_remote.return_value = {
                "name": "nginx",
                "tags": [{
                    "name": "latest",
                    "last_updated": "2024-01-01T12:00:00Z",
                    "full_size": 133700000
                }]
            }
            
            result = await command.execute(image_name="nginx")
            
            assert isinstance(result, SuccessResult)
            assert result.data["status"] == "success"
            assert result.data["total_local_images"] == 1
            assert result.data["compared_images"] == 1
            assert len(result.data["comparison_results"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_compare_all_local(self, command):
        """Test comparing all local images."""
        with patch.object(command, '_get_local_images') as mock_local, \
             patch.object(command, '_get_remote_image_info') as mock_remote:
            
            mock_local.return_value = [
                {"Repository": "nginx", "Tag": "latest"},
                {"Repository": "ubuntu", "Tag": "20.04"}
            ]
            
            mock_remote.return_value = {
                "name": "nginx",
                "tags": [{"name": "latest"}]
            }
            
            result = await command.execute(include_all_local=True)
            
            assert isinstance(result, SuccessResult)
            assert result.data["total_local_images"] == 2
            assert result.data["compared_images"] == 2
    
    @pytest.mark.asyncio
    async def test_execute_dangling_image(self, command):
        """Test handling dangling images."""
        with patch.object(command, '_get_local_images') as mock_local:
            mock_local.return_value = [{
                "Repository": "<none>",
                "Tag": "<none>",
                "CreatedAt": "2024-01-01T10:00:00Z",
                "Size": "100MB"
            }]
            
            result = await command.execute(include_dangling=True)
            
            assert isinstance(result, SuccessResult)
            assert result.data["total_local_images"] == 1
            assert result.data["comparison_results"][0]["comparison"]["status"] == "dangling_or_invalid"
    
    @pytest.mark.asyncio
    async def test_execute_no_remote_found(self, command):
        """Test handling when no remote image is found."""
        with patch.object(command, '_get_local_images') as mock_local, \
             patch.object(command, '_get_remote_image_info') as mock_remote:
            
            mock_local.return_value = [{
                "Repository": "custom/image",
                "Tag": "latest"
            }]
            
            mock_remote.return_value = None
            
            result = await command.execute(image_name="custom/image")
            
            assert isinstance(result, SuccessResult)
            comparison = result.data["comparison_results"][0]["comparison"]
            assert comparison["status"] == "no_remote_found"
            assert not comparison["has_remote"]
    
    def test_parse_size(self, command):
        """Test size parsing."""
        assert command._parse_size("100MB") == 104857600
        assert command._parse_size("1GB") == 1073741824
        assert command._parse_size("500KB") == 512000
        assert command._parse_size("1000") == 1000
        assert command._parse_size("invalid") == 0
    
    def test_generate_summary(self, command):
        """Test summary generation."""
        comparison_results = [
            {
                "comparison": {"has_remote": True, "update_available": True}
            },
            {
                "comparison": {"has_remote": True, "update_available": False}
            },
            {
                "comparison": {"has_remote": False, "update_available": False}
            }
        ]
        
        summary = command._generate_summary(comparison_results)
        
        assert summary["total_images"] == 3
        assert summary["with_remote_counterpart"] == 2
        assert summary["updates_available"] == 1
        assert summary["no_remote_found"] == 1
        assert summary["update_percentage"] == pytest.approx(33.33, 0.01)
    
    def test_get_schema(self, command):
        """Test schema generation."""
        schema = command.get_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "image_name" in schema["properties"]
        assert "include_all_local" in schema["properties"]
        assert "check_updates" in schema["properties"]


class TestIntegration:
    """Integration tests for Docker image commands."""
    
    @pytest.mark.asyncio
    async def test_workflow_search_and_info(self):
        """Test workflow: search then get info."""
        hub_images_cmd = DockerHubImagesCommand()
        info_cmd = DockerHubImageInfoCommand()
        
        with patch('requests.get') as mock_get:
            # Mock search response
            search_response = Mock()
            search_response.status_code = 200
            search_response.json.return_value = {
                "count": 1,
                "results": [{
                    "repo_name": "library/nginx",
                    "name": "nginx",
                    "short_description": "Official nginx image"
                }]
            }
            search_response.url = "https://hub.docker.com/v2/search/repositories/"
            
            # Mock info response
            info_response = Mock()
            info_response.status_code = 200
            info_response.json.return_value = {
                "name": "nginx",
                "full_name": "library/nginx"
            }
            
            mock_get.side_effect = [search_response, info_response]
            
            # Search for images
            search_result = await hub_images_cmd.execute(query="nginx", limit=1)
            assert isinstance(search_result, SuccessResult)
            
            # Get detailed info
            info_result = await info_cmd.execute(image_name="library/nginx")
            assert isinstance(info_result, SuccessResult)
    
    @pytest.mark.asyncio
    async def test_error_handling_consistency(self):
        """Test that all commands handle errors consistently."""
        commands = [
            DockerHubImagesCommand(),
            DockerHubImageInfoCommand(),
            DockerImagesCompareCommand()
        ]
        
        for cmd in commands:
            # Test with invalid parameters
            if hasattr(cmd, 'execute'):
                result = await cmd.execute()
                assert isinstance(result, (SuccessResult, ErrorResult))


if __name__ == "__main__":
    pytest.main([__file__]) 