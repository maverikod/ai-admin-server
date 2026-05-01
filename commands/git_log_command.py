from mcp_proxy_adapter.core.errors import CommandError as CustomError
"""Git log command for showing commit history.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitLogCommand(BaseUnifiedCommand):
    """Show Git commit history.

    This command supports various Git log operations including:
    - Show commit history
    - Filter by author, date, file
    - Show specific number of commits
    - Pretty format output
    - Graph visualization
    - Search commits
    """

    name = "git_log"

    def __init__(self):
        """Initialize Git log command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        committer: Optional[str] = None,
        grep: Optional[str] = None,
        files: Optional[List[str]] = None,
        pretty: Optional[str] = None,
        graph: bool = False,
        oneline: bool = False,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git log command with unified security.

        Args:
            max_count: Maximum number of commits to show
            since: Show commits since date
            until: Show commits until date
            author: Filter by author
            committer: Filter by committer
            grep: Search commit messages
            files: Filter by files
            pretty: Pretty format
            graph: Show graph
            oneline: One line per commit
            user_roles: List of user roles for security validation

        Returns:
            Success result with log information
        """
        # Use unified security approach
        return await super().execute(
            max_count=max_count,
            since=since,
            until=until,
            author=author,
            committer=committer,
            grep=grep,
            files=files,
            pretty=pretty,
            graph=graph,
            oneline=oneline,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git log command."""
        return "git:log"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git log command logic."""
        return await self._show_log(**kwargs)

    async def _show_log(
        self,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        author: Optional[str] = None,
        committer: Optional[str] = None,
        grep: Optional[str] = None,
        files: Optional[List[str]] = None,
        pretty: Optional[str] = None,
        graph: bool = False,
        oneline: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Show Git commit history."""
        try:
            # Build Git command
            cmd = ["git", "log"]

            # Add options
            if max_count:
                cmd.extend(["--max-count", str(max_count)])
            if since:
                cmd.extend(["--since", since])
            if until:
                cmd.extend(["--until", until])
            if author:
                cmd.extend(["--author", author])
            if committer:
                cmd.extend(["--committer", committer])
            if grep:
                cmd.extend(["--grep", grep])
            if pretty:
                cmd.extend(["--pretty", pretty])
            if graph:
                cmd.append("--graph")
            if oneline:
                cmd.append("--oneline")

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise CustomError(f"Git log failed: {result.stderr}")

            # Parse commits
            commits = []
            if result.stdout.strip():
                commits = result.stdout.strip().split("\n")

            return {
                "message": f"Git log completed successfully",
                "max_count": max_count,
                "since": since,
                "until": until,
                "author": author,
                "committer": committer,
                "grep": grep,
                "files": files,
                "pretty": pretty,
                "graph": graph,
                "oneline": oneline,
                "commits": commits,
                "count": len(commits),
                "raw_output": result.stdout,
                    "command": " ".join(cmd),
                }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git log command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git log failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git log command parameters."""
        return {
            "type": "object",
            "properties": {
                "max_count": {
                    "type": "integer",
                    "description": "Maximum number of commits to show",
                },
                "since": {
                    "type": "string",
                    "description": "Show commits since date",
                },
                "until": {
                    "type": "string",
                    "description": "Show commits until date",
                },
                "author": {
                    "type": "string",
                    "description": "Filter by author",
                },
                "committer": {
                    "type": "string",
                    "description": "Filter by committer",
                },
                "grep": {
                    "type": "string",
                    "description": "Search commit messages",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by files",
                },
                "pretty": {
                    "type": "string",
                    "description": "Pretty format",
                },
                "graph": {
                    "type": "boolean",
                    "description": "Show graph",
                    "default": False,
                },
                "oneline": {
                    "type": "boolean",
                    "description": "One line per commit",
                    "default": False,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "additionalProperties": False,
        }
