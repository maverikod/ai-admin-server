"""
Enhanced Docker Search Command

This command combines Docker CLI search with API details to provide
comprehensive search results for Docker images.
"""

import asyncio
import json
import re
import requests
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerSearchCommand(Command):
    """Docker search command that combines CLI and API methods."""
    
    name = "docker_search"
    
    async def execute(
        self,
        query: str,
        limit: Optional[int] = None,
        filter_stars: Optional[int] = None,
        filter_official: bool = False,
        filter_automated: bool = False,
        include_details: bool = True,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker search using API.
        
        Args:
            query: Search query for image names
            limit: Maximum number of results
            filter_stars: Minimum number of stars
            filter_official: Show only official images
            filter_automated: Show only automated builds
            include_details: Include detailed information from API
            
        Returns:
            Success result with search results
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Search using API
            api_results = await self._search_with_api(
                query, limit, filter_stars, filter_official, filter_automated
            )
            
            # Step 2: Enhance with API details if requested
            enhanced_results = []
            if include_details and api_results:
                for result in api_results[:10]:  # Limit to first 10 for API calls
                    try:
                        details = await self._get_image_details(result["name"])
                        result.update(details)
                    except Exception as e:
                        # If API call fails, keep result as is
                        result["api_error"] = str(e)
                    enhanced_results.append(result)
            else:
                enhanced_results = api_results
            
            end_time = datetime.now()
            
            return SuccessResult(data={
                "status": "success",
                "query": query,
                "total_count": len(enhanced_results),
                "results_count": len(enhanced_results),
                "results": enhanced_results,
                "search_params": {
                    "limit": limit,
                    "filter_stars": filter_stars,
                    "filter_official": filter_official,
                    "filter_automated": filter_automated,
                    "include_details": include_details
                },
                "search_method": "api_search",
                "timestamp": end_time.isoformat(),
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000
            })
            
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="DOCKER_SEARCH_ENHANCED_ERROR",
                data=getattr(e, 'data', {})
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during enhanced Docker search: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
    async def _search_with_api(self, query: str, limit: Optional[int], 
                              filter_stars: Optional[int], filter_official: bool, 
                              filter_automated: bool) -> List[Dict[str, Any]]:
        """Search using Docker Hub API."""
        try:
            # Get Bearer token
            bearer_token = await self._get_bearer_token()
            
            results = []
            
            # Step 1: Search in user's own repositories first
            if bearer_token:
                user_results = await self._search_user_repositories(query, bearer_token, limit)
                results.extend(user_results)
            
            # Step 2: Search in library (official images)
            if filter_official:
                library_results = await self._search_library_images(query, limit)
                results.extend(library_results)
            
            # Step 3: Search in specific namespaces
            if not filter_official:
                namespace_results = await self._search_namespace_images(query, limit)
                results.extend(namespace_results)
            
            # Step 4: Try search endpoint (usually doesn't work)
            if not results:
                search_results = await self._search_with_endpoint(query, limit, bearer_token)
                results.extend(search_results)
            
            # Filter by stars if specified
            if filter_stars:
                results = [r for r in results if r.get("stars", 0) >= filter_stars]
            
            # Limit results
            if limit:
                results = results[:limit]
            
            return results
            
        except Exception as e:
            # Fallback to popular images
            return await self._get_popular_images_and_filter(query, limit, filter_official)
    
    async def _search_user_repositories(self, query: str, bearer_token: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Search in user's own repositories."""
        try:
            # Get username from config
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                username = config.get("docker", {}).get("username", "vasilyvz@gmail.com")
                # Extract username from email
                username_hub = username.split('@')[0] if '@' in username else username
            else:
                username_hub = "vasilyvz"
            
            # Get user's repositories
            api_url = f"https://hub.docker.com/v2/repositories/{username_hub}/"
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0",
                "Authorization": f"Bearer {bearer_token}"
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for repo in data.get("results", []):
                    # Filter by query
                    if query.lower() in repo.get("name", "").lower():
                        result = {
                            "name": f"{username_hub}/{repo.get('name', '')}",
                            "description": repo.get("description", ""),
                            "stars": repo.get("star_count", 0),
                            "is_official": False,
                            "is_automated": False,
                            "pull_count": repo.get("pull_count", 0),
                            "last_updated": repo.get("last_updated", ""),
                            "namespace": username_hub,
                            "user": username_hub,
                            "is_own": True
                        }
                        results.append(result)
                
                return results
            
            return []
            
        except Exception:
            return []
    
    async def _search_library_images(self, query: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Search in library (official images)."""
        try:
            api_url = "https://hub.docker.com/v2/repositories/library/"
            params = {
                "page_size": limit or 50,
                "page": 1
            }
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for repo in data.get("results", []):
                    # Filter by query
                    if query.lower() in repo.get("name", "").lower():
                        result = {
                            "name": repo.get("name", ""),
                            "description": repo.get("description", ""),
                            "stars": repo.get("star_count", 0),
                            "is_official": True,
                            "is_automated": False,
                            "pull_count": repo.get("pull_count", 0),
                            "last_updated": repo.get("last_updated", ""),
                            "namespace": "library",
                            "user": "library",
                            "is_own": False
                        }
                        results.append(result)
                
                return results
            
            return []
            
        except Exception:
            return []
    
    async def _search_namespace_images(self, query: str, limit: Optional[int]) -> List[Dict[str, Any]]:
        """Search in specific namespaces."""
        try:
            results = []
            
            # Try searching in namespace with same name as query
            api_url = f"https://hub.docker.com/v2/repositories/{query}/"
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                for repo in data.get("results", [])[:limit or 10]:
                    result = {
                        "name": f"{query}/{repo.get('name', '')}",
                        "description": repo.get("description", ""),
                        "stars": repo.get("star_count", 0),
                        "is_official": False,
                        "is_automated": False,
                        "pull_count": repo.get("pull_count", 0),
                        "last_updated": repo.get("last_updated", ""),
                        "namespace": query,
                        "user": query,
                        "is_own": False
                    }
                    results.append(result)
            
            return results
            
        except Exception:
            return []
    
    async def _search_with_endpoint(self, query: str, limit: Optional[int], bearer_token: Optional[str]) -> List[Dict[str, Any]]:
        """Search using search endpoint (usually doesn't work)."""
        try:
            api_url = "https://hub.docker.com/v2/search/repositories/"
            params = {
                "q": query,
                "page_size": limit or 20,
                "page": 1
            }
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            if bearer_token:
                headers["Authorization"] = f"Bearer {bearer_token}"
            
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for repo in data.get("results", []):
                    result = {
                        "name": repo.get("name", ""),
                        "description": repo.get("description", ""),
                        "stars": repo.get("star_count", 0),
                        "is_official": repo.get("is_official", False),
                        "is_automated": repo.get("is_automated", False),
                        "pull_count": repo.get("pull_count", 0),
                        "last_updated": repo.get("last_updated", ""),
                        "namespace": repo.get("namespace", ""),
                        "user": repo.get("user", ""),
                        "is_own": False
                    }
                    results.append(result)
                
                return results
            
            return []
            
        except Exception:
            return []
    
    async def _get_popular_images_and_filter(self, query: str, limit: Optional[int], 
                                           filter_official: bool) -> List[Dict[str, Any]]:
        """Get popular images and filter by query."""
        try:
            # Get popular official images
            api_url = "https://hub.docker.com/v2/repositories/library/"
            params = {
                "page_size": 50,
                "page": 1
            }
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            for repo in data.get("results", []):
                # Filter by query
                if query.lower() in repo.get("name", "").lower():
                    result = {
                        "name": repo.get("name", ""),
                        "description": repo.get("description", ""),
                        "stars": repo.get("star_count", 0),
                        "is_official": True,
                        "is_automated": False,
                        "pull_count": repo.get("pull_count", 0),
                        "last_updated": repo.get("last_updated", ""),
                        "namespace": repo.get("namespace", ""),
                        "user": repo.get("user", "")
                    }
                    results.append(result)
                    
                    if limit and len(results) >= limit:
                        break
            
            return results
            
        except Exception:
            return []
    
    def _parse_docker_search_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse docker search command output."""
        results = []
        
        if not output:
            return results
        
        lines = output.splitlines()
        if len(lines) < 2:  # Need at least header and one result
            return results
        
        # Skip header line
        data_lines = lines[1:]
        
        for line in data_lines:
            if line.strip():
                # Parse line: NAME DESCRIPTION STARS OFFICIAL AUTOMATED
                parts = line.split()
                if len(parts) >= 5:
                    # Handle description that might contain spaces
                    name = parts[0]
                    stars = parts[-3]
                    official = parts[-2]
                    automated = parts[-1]
                    
                    # Description is everything between name and stars
                    description_parts = parts[1:-3]
                    description = " ".join(description_parts) if description_parts else ""
                    
                    results.append({
                        "name": name,
                        "description": description,
                        "stars": int(stars) if stars.isdigit() else 0,
                        "is_official": official == "[OK]",
                        "is_automated": automated == "[OK]"
                    })
        
        return results
    
    async def _get_image_details(self, image_name: str) -> Dict[str, Any]:
        """Get detailed information about an image from Docker Hub API."""
        try:
            # Get Bearer token
            bearer_token = await self._get_bearer_token()
            
            # Build API URL
            api_url = f"https://hub.docker.com/v2/repositories/{image_name}/"
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            # Try with Bearer token first
            if bearer_token:
                headers["Authorization"] = f"Bearer {bearer_token}"
                response = requests.get(api_url, headers=headers, timeout=10)
                
                if response.status_code == 401:
                    # Token expired, try to get new one
                    bearer_token = await self._get_bearer_token()
                    if bearer_token:
                        headers["Authorization"] = f"Bearer {bearer_token}"
                        response = requests.get(api_url, headers=headers, timeout=10)
                    else:
                        # No token available, try without authentication
                        headers.pop("Authorization", None)
                        response = requests.get(api_url, headers=headers, timeout=10)
            else:
                # No token available, try without authentication
                response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "full_description": data.get("full_description", ""),
                    "pull_count": data.get("pull_count", 0),
                    "last_updated": data.get("last_updated", ""),
                    "affiliation": data.get("affiliation", ""),
                    "user": data.get("user", ""),
                    "namespace": data.get("namespace", ""),
                    "repository_type": data.get("repository_type", ""),
                    "status": data.get("status", ""),
                    "api_details_available": True
                }
            else:
                return {"api_details_available": False, "api_error": f"Status {response.status_code}"}
                
        except Exception as e:
            return {"api_details_available": False, "api_error": str(e)}
    
    async def _get_bearer_token(self) -> Optional[str]:
        """Get Bearer token from Docker Hub using Personal Access Token."""
        try:
            # Get PAT from config
            pat = self._get_docker_auth_token()
            if not pat:
                return None
            
            # Get username from config
            username = self._get_docker_username()
            if not username:
                return None
            
            # Request Bearer token
            auth_url = "https://hub.docker.com/v2/users/login"
            auth_data = {
                "username": username,
                "password": pat
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.post(auth_url, json=auth_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("token")
            else:
                return None
                
        except Exception:
            return None
    
    async def _get_bearer_token(self) -> Optional[str]:
        """Get Docker Bearer token from Personal Access Token."""
        try:
            # Get PAT from config
            pat_token = self._get_docker_auth_token()
            if not pat_token:
                return None
            
            # Get username from config
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                username = config.get("docker", {}).get("username", "vasilyvz@gmail.com")
            else:
                username = "vasilyvz@gmail.com"
            
            # Request Bearer token
            auth_url = "https://hub.docker.com/v2/users/login"
            auth_data = {
                "username": username,
                "password": pat_token
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            response = requests.post(auth_url, json=auth_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("token")
            else:
                return None
                
        except Exception:
            return None
    
    def _get_docker_auth_token(self) -> Optional[str]:
        """Get Docker authentication token from server config."""
        try:
            # Try to get token from server config
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check for docker section
                if "docker" in config and "token" in config["docker"]:
                    token = config["docker"]["token"]
                    
                    # Clean up token if needed
                    if token.startswith("dckr_pat_"):
                        # This is a Docker Hub Personal Access Token
                        return token
                    elif token.startswith("ghp_"):
                        # This looks like a GitHub token, not Docker
                        return None
                    else:
                        return token
            
            return None
        except Exception:
            return None
    
    def _get_docker_username(self) -> Optional[str]:
        """Get Docker username from server config."""
        try:
            # Try to get username from server config
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Check for docker section
                if "docker" in config and "username" in config["docker"]:
                    return config["docker"]["username"]
            
            return None
        except Exception:
            return None
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for enhanced Docker search command parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for image names",
                    "examples": ["nginx", "ubuntu", "python", "node"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 100
                },
                "filter_stars": {
                    "type": "integer",
                    "description": "Minimum number of stars",
                    "minimum": 0
                },
                "filter_official": {
                    "type": "boolean",
                    "description": "Show only official images",
                    "default": False
                },
                "filter_automated": {
                    "type": "boolean",
                    "description": "Show only automated builds",
                    "default": False
                },
                "include_details": {
                    "type": "boolean",
                    "description": "Include detailed information from API",
                    "default": True
                }
            },
            "required": ["query"],
            "additionalProperties": False
        } 