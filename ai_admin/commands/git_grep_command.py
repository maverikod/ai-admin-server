from ai_admin.core.custom_exceptions import CustomError
"""Git grep command for searching in Git repository.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import subprocess
from typing import Dict, Any, Optional, List
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from ai_admin.commands.base_unified_command import BaseUnifiedCommand
from ai_admin.security.git_security_adapter import GitSecurityAdapter

class GitGrepCommand(BaseUnifiedCommand):
    """Search for patterns in Git repository.

    This command supports various Git grep operations including:
    - Search in working directory
    - Search in specific commits
    - Case insensitive search
    - Regular expression search
    - Show line numbers
    - Show file names only
    - Search in specific files
    """

    name = "git_grep"

    def __init__(self):
        """Initialize Git grep command."""
        super().__init__()
        self.security_adapter = GitSecurityAdapter()

    async def execute(
        self,
        pattern: str,
        files: Optional[List[str]] = None,
        commit: Optional[str] = None,
        case_insensitive: bool = False,
        regex: bool = False,
        extended_regex: bool = False,
        fixed_strings: bool = False,
        line_number: bool = True,
        show_filename: bool = True,
        user_roles: Optional[List[str]] = None,
        **kwargs,
    ) -> SuccessResult:
        """Execute Git grep command with unified security.

        Args:
            pattern: Search pattern
            files: List of files to search in
            commit: Commit to search in
            case_insensitive: Case insensitive search
            regex: Regular expression search
            extended_regex: Extended regular expression
            fixed_strings: Fixed string search
            line_number: Show line numbers
            show_filename: Show file names
            user_roles: List of user roles for security validation

        Returns:
            Success result with grep information
        """
        # Validate inputs
        if not pattern:
            return ErrorResult(message="Search pattern is required", code="VALIDATION_ERROR")

        # Use unified security approach
        return await super().execute(
            pattern=pattern,
            files=files,
            commit=commit,
            case_insensitive=case_insensitive,
            regex=regex,
            extended_regex=extended_regex,
            fixed_strings=fixed_strings,
            line_number=line_number,
            show_filename=show_filename,
            user_roles=user_roles,
            **kwargs,
        )

    def _get_default_operation(self) -> str:
        """Get default operation name for Git grep command."""
        return "git:grep"

    async def _execute_command_logic(self, **kwargs) -> Dict[str, Any]:
        """Execute Git grep command logic."""
        return await self._grep(**kwargs)

    async def _grep(
        self,
        pattern: str,
        files: Optional[List[str]] = None,
        commit: Optional[str] = None,
        case_insensitive: bool = False,
        regex: bool = False,
        extended_regex: bool = False,
        fixed_strings: bool = False,
        line_number: bool = True,
        show_filename: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Search for pattern in Git repository."""
        try:
            # Build Git command
            cmd = ["git", "grep"]

            # Add options
            if case_insensitive:
                cmd.append("-i")
            if regex:
                cmd.append("-E")
            elif extended_regex:
                cmd.append("-E")
            if fixed_strings:
                cmd.append("-F")
            if not line_number:
                cmd.append("-n")
            if not show_filename:
                cmd.append("-h")

            # Add pattern
            cmd.append(pattern)

            # Add commit if specified
            if commit:
                cmd.append(commit)

            # Add files if specified
            if files:
                cmd.extend(files)

            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                # Git grep returns non-zero when no matches found, which is not an error
                if "No match" in result.stderr or "fatal" not in result.stderr:
                    return {
                        "message": f"No matches found for pattern '{pattern}'",
                        "pattern": pattern,
                        "files": files,
                        "commit": commit,
                        "case_insensitive": case_insensitive,
                        "regex": regex,
                        "extended_regex": extended_regex,
                        "fixed_strings": fixed_strings,
                        "line_number": line_number,
                        "show_filename": show_filename,
                        "matches": [],
                        "count": 0,
                        "raw_output": result.stdout,
                        "command": " ".join(cmd),
                    }
                else:
                    raise CustomError(f"Git grep failed: {result.stderr}")

            # Parse results
            matches = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    matches.append(line.strip())

            return {
                "message": f"Found {len(matches)} matches for pattern '{pattern}'",
                "pattern": pattern,
                "files": files,
                "commit": commit,
                "case_insensitive": case_insensitive,
                "regex": regex,
                "extended_regex": extended_regex,
                "fixed_strings": fixed_strings,
                "line_number": line_number,
                "show_filename": show_filename,
                "matches": matches,
                "count": len(matches),
                "raw_output": result.stdout,
                "command": " ".join(cmd),
            }

        except subprocess.TimeoutExpired as e:
            raise CustomError(f"Git grep command timed out: {str(e)}")
        except CustomError as e:
            raise CustomError(f"Git grep failed: {str(e)}")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for Git grep command parameters."""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of files to search in",
                },
                "commit": {
                    "type": "string",
                    "description": "Commit to search in",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search",
                    "default": False,
                },
                "regex": {
                    "type": "boolean",
                    "description": "Regular expression search",
                    "default": False,
                },
                "extended_regex": {
                    "type": "boolean",
                    "description": "Extended regular expression",
                    "default": False,
                },
                "fixed_strings": {
                    "type": "boolean",
                    "description": "Fixed string search",
                    "default": False,
                },
                "line_number": {
                    "type": "boolean",
                    "description": "Show line numbers",
                    "default": True,
                },
                "show_filename": {
                    "type": "boolean",
                    "description": "Show file names",
                    "default": True,
                },
                "user_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of user roles for security validation",
                },
            },
            "required": ["pattern"],
            "additionalProperties": False,
        }
