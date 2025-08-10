"""Docker search CLI command for searching Docker images using docker CLI."""

import asyncio
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError


class DockerSearchCLICommand(Command):
    """Search Docker images using Docker CLI.
    
    This command uses the docker search command to find images
    in Docker Hub with proper authentication.
    """
    
    name = "docker_search_cli"
    
    async def execute(
        self,
        query: str,
        limit: Optional[int] = None,
        filter_stars: Optional[int] = None,
        filter_official: bool = False,
        filter_automated: bool = False,
        **kwargs
    ) -> SuccessResult:
        """Execute Docker search using CLI.
        
        Args:
            query: Search query for image names
            limit: Maximum number of results
            filter_stars: Minimum number of stars
            filter_official: Show only official images
            filter_automated: Show only automated builds
            
        Returns:
            Success result with search results
        """
        try:
            start_time = datetime.now()
            
            # Build docker search command
            cmd = ["docker", "search"]
            
            # Add filters
            if filter_official:
                cmd.append("--filter=is-official=true")
            if filter_automated:
                cmd.append("--filter=is-automated=true")
            if filter_stars:
                cmd.append(f"--filter=stars={filter_stars}")
            if limit:
                cmd.append(f"--limit={limit}")
            
            # Add query
            cmd.append(query)
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            end_time = datetime.now()
            
            if process.returncode != 0:
                error_output = stderr.decode('utf-8')
                raise CommandError(
                    f"Docker search command failed with exit code {process.returncode}",
                    data={
                        "stderr": error_output,
                        "command": " ".join(cmd),
                        "exit_code": process.returncode
                    }
                )
            
            # Parse output
            output = stdout.decode('utf-8').strip()
            results = self._parse_docker_search_output(output)
            
            return SuccessResult(data={
                "status": "success",
                "query": query,
                "total_count": len(results),
                "results_count": len(results),
                "results": results,
                "search_params": {
                    "limit": limit,
                    "filter_stars": filter_stars,
                    "filter_official": filter_official,
                    "filter_automated": filter_automated
                },
                "command": " ".join(cmd),
                "timestamp": end_time.isoformat(),
                "execution_time_ms": (end_time - start_time).total_seconds() * 1000
            })
            
        except CommandError as e:
            return ErrorResult(
                message=str(e),
                code="DOCKER_SEARCH_CLI_ERROR",
                data=getattr(e, 'data', {})
            )
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during Docker search: {str(e)}",
                code="INTERNAL_ERROR"
            )
    
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
    
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Docker search CLI command parameters."""
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
                }
            },
            "required": ["query"],
            "additionalProperties": False
        } 