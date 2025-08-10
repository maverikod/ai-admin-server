"""Docker Hub images command for viewing remote Docker images."""

import asyncio
import json
import requests
import base64
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerHubImagesCommand(Command):
    """View and search Docker images in Docker Hub.
    
    This command allows viewing remote Docker images from Docker Hub,
    including official images, user repositories, and detailed metadata.
    """
    
    name = "docker_hub_images"
    
    async def execute(
        self,
        query: Optional[str] = None,
        username: Optional[str] = None,
        repository: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
        official_only: bool = False,
        automated_only: bool = False,
        sort_by: str = "stars",
        order: str = "desc",
        include_tags: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker Hub images command.
        
        Args:
            query: Search query for image names
            username: Specific username to search in
            repository: Specific repository name
            limit: Maximum number of results (1-100)
            page: Page number for pagination
            official_only: Show only official images
            automated_only: Show only automated builds
            sort_by: Sort field (stars, pulls, name, updated)
            order: Sort order (asc, desc)
            include_tags: Include available tags in results
            
        Returns:
            Success result with Docker Hub images information
        """
        try:
            # Validate inputs
            if limit < 1 or limit > 100:
                raise CommandError("Limit must be between 1 and 100")
            
            if page < 1:
                raise CommandError("Page must be greater than 0")
            
            if sort_by not in ["stars", "pulls", "name", "updated"]:
                raise CommandError("Invalid sort_by parameter")
            
            if order not in ["asc", "desc"]:
                raise CommandError("Invalid order parameter")
            
            # Build API URL and parameters
            if repository and username:
                # Get specific repository
                api_url = f"https://hub.docker.com/v2/repositories/{username}/{repository}/"
                params = {}
            elif repository:
                # Search for repository
                api_url = "https://hub.docker.com/v2/search/repositories/"
                params = {
                    "q": repository,
                    "page_size": limit,
                    "page": page,
                    "ordering": f"{sort_by}_{order}"
                }
            elif username:
                # Get user's repositories
                api_url = f"https://hub.docker.com/v2/repositories/{username}/"
                params = {
                    "page_size": limit,
                    "page": page,
                    "ordering": f"{sort_by}_{order}"
                }
            elif query:
                # Search repositories - use multiple strategies
                results = await self._search_with_multiple_strategies(query, limit, page, sort_by, order)
                return SuccessResult(data={
                    "status": "success",
                    "query": query,
                    "username": username,
                    "repository": repository,
                    "total_count": len(results),
                    "results_count": len(results),
                    "page": page,
                    "limit": limit,
                    "results": results,
                    "search_params": {
                        "official_only": official_only,
                        "automated_only": automated_only,
                        "sort_by": sort_by,
                        "order": order,
                        "include_tags": include_tags
                    },
                    "api_url": "multiple_strategies",
                    "debug_info": {
                        "status_code": 200,
                        "url": "multiple_strategies",
                        "response_headers": {},
                        "data_keys": ["results"],
                        "results_count": len(results)
                    },
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": 0
                })
            else:
                # Get popular repositories
                api_url = "https://hub.docker.com/v2/search/repositories/"
                params = {
                    "page_size": limit,
                    "page": page,
                    "ordering": f"{sort_by}_{order}"
                }
            
            # Add filters
            if official_only:
                params["is_official"] = "true"
            if automated_only:
                params["is_automated"] = "true"
            
            # Get Docker auth token
            auth_token = self._get_docker_auth_token()
            
            # Make API request
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            if auth_token:
                headers["Authorization"] = f"JWT {auth_token}"
            
            start_time = datetime.now()
            
            response = requests.get(api_url, params=params, headers=headers, timeout=30)
            end_time = datetime.now()
            
            if response.status_code != 200:
                raise CommandError(
                    f"Docker Hub API request failed with status {response.status_code}",
                    data={
                        "status_code": response.status_code,
                        "response_text": response.text[:1000],
                        "url": response.url,
                        "headers": dict(response.headers)
                    }
                )
            
            data = response.json()
            
            # Debug info
            debug_info = {
                "status_code": response.status_code,
                "url": response.url,
                "response_headers": dict(response.headers),
                "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
                "results_count": len(data.get("results", [])) if isinstance(data, dict) else 0
            }
            
            # Process results
            if repository and username:
                # Single repository response
                repo_data = data
                results = [self._process_repository_data(repo_data)]
                total_count = 1
            else:
                # Multiple repositories response
                results = []
                for repo in data.get("results", []):
                    repo_info = self._process_repository_data(repo)
                    
                    # Get tags if requested
                    if include_tags and repo_info["name"]:
                        try:
                            tags = await self._get_repository_tags(repo_info["name"])
                            repo_info["tags"] = tags
                        except Exception:
                            repo_info["tags"] = []
                    
                    results.append(repo_info)
                
                total_count = data.get("count", len(results))
            
            return SuccessResult(data={
                "status": "success",
                "query": query,
                "username": username,
                "repository": repository,
                "total_count": total_count,
                "results_count": len(results),
                "page": page,
                "limit": limit,
                "results": results,
                "search_params": {
                    "official_only": official_only,
                    "automated_only": automated_only,
                    "sort_by": sort_by,
                    "order": order,
                    "include_tags": include_tags
                },
                "api_url": response.url,
                "debug_info": debug_info,
                "timestamp": end_time.isoformat(),
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000
            })
            
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="HUB_IMAGES_ERROR"
            )
        except requests.RequestException as e:
            return ErrorResult(
                message=f"Network error during Docker Hub API request: {str(e)}",
                code="NETWORK_ERROR"
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error viewing Docker Hub images: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
    def _process_repository_data(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process repository data from Docker Hub API."""
        return {
            "name": repo_data.get("repo_name", ""),
            "full_name": repo_data.get("name", ""),
            "description": repo_data.get("short_description", ""),
            "full_description": repo_data.get("full_description", ""),
            "is_official": repo_data.get("is_official", False),
            "is_automated": repo_data.get("is_automated", False),
            "star_count": repo_data.get("star_count", 0),
            "pull_count": repo_data.get("pull_count", 0),
            "last_updated": repo_data.get("last_updated", ""),
            "affiliation": repo_data.get("affiliation", ""),
            "user": repo_data.get("user", ""),
            "namespace": repo_data.get("namespace", ""),
            "repository_type": repo_data.get("repository_type", ""),
            "status": repo_data.get("status", ""),
            "tags": []  # Will be populated if include_tags=True
        }
    
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
    
    async def _search_with_multiple_strategies(self, query: str, limit: int, page: int, sort_by: str, order: str) -> List[Dict[str, Any]]:
        """Search using multiple strategies since /v2/search/repositories/ doesn't work."""
        results = []
        
        # Strategy 1: Search in user's own repositories
        try:
            bearer_token = await self._get_bearer_token()
            if bearer_token:
                user_results = await self._search_user_repositories(query, bearer_token, limit)
                results.extend(user_results)
        except Exception:
            pass
        
        # Strategy 2: Search in library (official images)
        try:
            library_results = await self._search_library_images(query, limit)
            results.extend(library_results)
        except Exception:
            pass
        
        # Strategy 3: Search in specific namespace
        try:
            namespace_results = await self._search_namespace_images(query, limit)
            results.extend(namespace_results)
        except Exception:
            pass
        
        # Strategy 4: Try the problematic search endpoint as last resort
        try:
            search_results = await self._search_with_endpoint(query, limit, None)
            results.extend(search_results)
        except Exception:
            pass
        
        # Sort results
        if sort_by == "stars":
            results.sort(key=lambda x: x.get("stars", 0), reverse=(order == "desc"))
        elif sort_by == "pulls":
            results.sort(key=lambda x: x.get("pull_count", 0), reverse=(order == "desc"))
        elif sort_by == "name":
            results.sort(key=lambda x: x.get("name", ""), reverse=(order == "desc"))
        elif sort_by == "updated":
            results.sort(key=lambda x: x.get("last_updated", ""), reverse=(order == "desc"))
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        return results[start_idx:end_idx]
    
    async def _get_bearer_token(self) -> Optional[str]:
        """Get Docker Bearer token from Personal Access Token."""
        try:
            pat_token = self._get_docker_auth_token()
            if not pat_token:
                return None
            
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                username = config.get("docker", {}).get("username", "vasilyvz@gmail.com")
            else:
                username = "vasilyvz@gmail.com"
            
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
    
    async def _search_user_repositories(self, query: str, bearer_token: str, limit: int) -> List[Dict[str, Any]]:
        """Search in user's own repositories."""
        try:
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                username = config.get("docker", {}).get("username", "vasilyvz@gmail.com")
                username_hub = username.split('@')[0] if '@' in username else username
            else:
                username_hub = "vasilyvz"
            
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
                
                return results[:limit]
            
            return []
            
        except Exception:
            return []
    
    async def _search_library_images(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search in library (official images)."""
        try:
            api_url = "https://hub.docker.com/v2/repositories/library/"
            params = {
                "page_size": limit * 2,  # Get more to filter
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
                
                return results[:limit]
            
            return []
            
        except Exception:
            return []
    
    async def _search_namespace_images(self, query: str, limit: int) -> List[Dict[str, Any]]:
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
                
                for repo in data.get("results", [])[:limit]:
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
    
    async def _search_with_endpoint(self, query: str, limit: int, bearer_token: Optional[str]) -> List[Dict[str, Any]]:
        """Search using search endpoint (usually doesn't work)."""
        try:
            api_url = "https://hub.docker.com/v2/search/repositories/"
            params = {
                "q": query,
                "page_size": limit,
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
    
    async def _get_repository_tags(self, repo_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get tags for a specific repository."""
        try:
            api_url = f"https://hub.docker.com/v2/repositories/{repo_name}/tags/"
            params = {
                "page_size": limit,
                "page": 1,
                "ordering": "last_updated"
            }
            
            # Get Docker auth token
            auth_token = self._get_docker_auth_token()
            
            headers = {
                "Accept": "application/json",
                "User-Agent": "AI-Admin-Server/1.0"
            }
            
            if auth_token:
                headers["Authorization"] = f"JWT {auth_token}"
            
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tags = []
                for tag in data.get("results", []):
                    tags.append({
                        "name": tag.get("name", ""),
                        "last_updated": tag.get("last_updated", ""),
                        "full_size": tag.get("full_size", 0),
                        "images": tag.get("images", [])
                    })
                return tags
            else:
                return []
                
        except Exception:
            return []
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker Hub images command parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for image names",
                    "examples": ["nginx", "ubuntu", "python", "node"]
                },
                "username": {
                    "type": "string",
                    "description": "Specific username to search in",
                    "examples": ["library", "nginx", "myusername"]
                },
                "repository": {
                    "type": "string",
                    "description": "Specific repository name",
                    "examples": ["nginx", "ubuntu", "myapp"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "page": {
                    "type": "integer",
                    "description": "Page number for pagination",
                    "minimum": 1,
                    "default": 1
                },
                "official_only": {
                    "type": "boolean",
                    "description": "Show only official images",
                    "default": False
                },
                "automated_only": {
                    "type": "boolean",
                    "description": "Show only automated builds",
                    "default": False
                },
                "sort_by": {
                    "type": "string",
                    "description": "Sort field",
                    "enum": ["stars", "pulls", "name", "updated"],
                    "default": "stars"
                },
                "order": {
                    "type": "string",
                    "description": "Sort order",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "include_tags": {
                    "type": "boolean",
                    "description": "Include available tags in results",
                    "default": False
                }
            },
            "required": [],
            "additionalProperties": False
        } 