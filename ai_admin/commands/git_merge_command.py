"""Git merge command for merging branches in Git."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitMergeCommand(Command):
    """Merge Git branches.
    
    This command supports:
    - Fast-forward merge
    - No-fast-forward merge
    - Squash merge
    - Merge specific commits
    - Abort merge
    - Continue merge
    """
    
    name = "git_merge"
    
    async def execute(
        self,
        current_directory: str,
        branch: str,
        commit: Optional[str] = None,
        no_ff: bool = False,
        squash: bool = False,
        abort: bool = False,
        continue_merge: bool = False,
        message: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        strategy: Optional[str] = None,
        strategy_option: Optional[str] = None,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Merge Git branches.
        
        Args:
            current_directory: Current working directory where to execute git commands
            branch: Branch to merge into current branch
            commit: Specific commit to merge (optional)
            no_ff: Create merge commit even if fast-forward is possible
            squash: Squash commits into one
            abort: Abort current merge
            continue_merge: Continue merge after resolving conflicts
            message: Merge commit message
            quiet: Suppress output
            verbose: Show detailed output
            strategy: Merge strategy (recursive, octopus, ours, subtree)
            strategy_option: Strategy option
            repository_path: Path to repository (optional, defaults to current_directory)
        """
        try:
            # Validate current_directory
            if not current_directory:
                return ErrorResult(
                    message="current_directory is required",
                    code="MISSING_CURRENT_DIRECTORY",
                    details={}
                )
            
            if not os.path.exists(current_directory):
                return ErrorResult(
                    message=f"Directory '{current_directory}' does not exist",
                    code="DIRECTORY_NOT_FOUND",
                    details={"current_directory": current_directory}
                )
            
            # Determine repository path
            if not repository_path:
                repository_path = current_directory
            
            # Check if directory is a Git repository
            if not os.path.exists(os.path.join(repository_path, ".git")):
                return ErrorResult(
                    message=f"'{repository_path}' is not a Git repository",
                    code="NOT_GIT_REPOSITORY",
                    details={"repository_path": repository_path}
                )
            
            # Build git merge command
            cmd = ["git", "merge"]
            
            if abort:
                cmd.append("--abort")
            elif continue_merge:
                cmd.append("--continue")
            else:
                # Validate branch or commit
                if not branch and not commit:
                    return ErrorResult(
                        message="Either branch or commit must be specified",
                        code="MISSING_BRANCH_OR_COMMIT",
                        details={}
                    )
                
                if no_ff:
                    cmd.append("--no-ff")
                    # For no-ff merges, we need a message to avoid editor
                    if not message:
                        message = f"Merge branch '{branch or commit}'"
                
                if squash:
                    cmd.append("--squash")
                
                if message:
                    cmd.extend(["-m", message])
                
                if quiet:
                    cmd.append("--quiet")
                
                if verbose:
                    cmd.append("--verbose")
                
                if strategy:
                    cmd.extend(["--strategy", strategy])
                
                if strategy_option:
                    cmd.extend(["--strategy-option", strategy_option])
                
                # Add branch or commit to merge
                if commit:
                    cmd.append(commit)
                else:
                    cmd.append(branch)
            
            # Execute git merge
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                # Check if merge has conflicts
                if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
                    return ErrorResult(
                        message="Merge has conflicts that need to be resolved",
                        code="MERGE_CONFLICT",
                        details={
                            "command": " ".join(cmd),
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "conflict_files": await self._get_conflict_files(repository_path)
                        }
                    )
                
                return ErrorResult(
                    message=f"Git merge failed: {result.stderr}",
                    code="GIT_MERGE_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get merge results
            merge_info = await self._get_merge_info(repository_path)
            
            return SuccessResult(data={
                "message": f"Successfully merged {'aborted' if abort else branch or commit}",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "merge_info": merge_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git merge: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_merge_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about merge result."""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            current_branch = ""
            if result.returncode == 0:
                current_branch = result.stdout.strip()
            
            # Get recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            recent_commits = []
            if result.returncode == 0:
                recent_commits = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            return {
                "current_branch": current_branch,
                "recent_commits": recent_commits,
                "total_recent_commits": len(recent_commits)
            }
            
        except Exception:
            return {
                "current_branch": "",
                "recent_commits": [],
                "total_recent_commits": 0
            }
    
    async def _get_conflict_files(self, repo_path: str) -> List[str]:
        """Get list of files with conflicts."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            return []
            
        except Exception:
            return [] 