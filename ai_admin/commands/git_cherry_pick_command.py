"""Git cherry-pick command for applying specific commits."""

import os
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

from mcp_proxy_adapter.commands.base import Command
from mcp_proxy_adapter.commands.result import SuccessResult, ErrorResult
from mcp_proxy_adapter.core.errors import CommandError, ValidationError


class GitCherryPickCommand(Command):
    """Apply specific commits to current branch.
    
    This command supports:
    - Cherry-pick single commit
    - Cherry-pick multiple commits
    - Continue cherry-pick after conflicts
    - Abort cherry-pick
    - Skip commit
    - Edit commit message
    - Sign commits
    """
    
    name = "git_cherry_pick"
    
    async def execute(
        self,
        current_directory: str,
        commits: List[str],
        continue_pick: bool = False,
        abort: bool = False,
        skip: bool = False,
        edit: bool = False,
        signoff: bool = False,
        sign: bool = False,
        no_commit: bool = False,
        fast_forward: bool = False,
        mainline: Optional[int] = None,
        strategy: Optional[str] = None,
        strategy_option: Optional[str] = None,
        quiet: bool = False,
        verbose: bool = False,
        repository_path: Optional[str] = None,
        **kwargs
    ):
        """
        Apply specific commits to current branch.
        
        Args:
            current_directory: Current working directory where to execute git commands
            commits: List of commit hashes to cherry-pick
            continue_pick: Continue cherry-pick after resolving conflicts
            abort: Abort cherry-pick
            skip: Skip current commit in cherry-pick
            edit: Edit commit message
            signoff: Add Signed-off-by line
            sign: Sign the commit
            no_commit: Don't create commit, just stage changes
            fast_forward: Use fast-forward mode
            mainline: Mainline parent number for merge commits
            strategy: Merge strategy (recursive, octopus, ours, subtree)
            strategy_option: Strategy option
            quiet: Suppress output
            verbose: Show detailed output
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
            
            # Build git cherry-pick command
            cmd = ["git", "cherry-pick"]
            
            if continue_pick:
                cmd.append("--continue")
            elif abort:
                cmd.append("--abort")
            elif skip:
                cmd.append("--skip")
            else:
                # Validate commits
                if not commits:
                    return ErrorResult(
                        message="At least one commit must be specified",
                        code="MISSING_COMMITS",
                        details={}
                    )
                
                if edit:
                    cmd.append("-e")
                
                if signoff:
                    cmd.append("-s")
                
                if sign:
                    cmd.append("--gpg-sign")
                
                if no_commit:
                    cmd.append("-n")
                
                if fast_forward:
                    cmd.append("--ff")
                
                if mainline:
                    cmd.extend(["-m", str(mainline)])
                
                if strategy:
                    cmd.extend(["--strategy", strategy])
                
                if strategy_option:
                    cmd.extend(["--strategy-option", strategy_option])
                
                if quiet:
                    cmd.append("--quiet")
                
                if verbose:
                    cmd.append("--verbose")
                
                # Add commits
                cmd.extend(commits)
            
            # Execute git cherry-pick
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=repository_path
            )
            
            if result.returncode != 0:
                # Check if cherry-pick has conflicts
                if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
                    return ErrorResult(
                        message="Cherry-pick has conflicts that need to be resolved",
                        code="CHERRY_PICK_CONFLICT",
                        details={
                            "command": " ".join(cmd),
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "conflict_files": await self._get_conflict_files(repository_path)
                        }
                    )
                
                return ErrorResult(
                    message=f"Git cherry-pick failed: {result.stderr}",
                    code="GIT_CHERRY_PICK_FAILED",
                    details={
                        "command": " ".join(cmd),
                        "stderr": result.stderr,
                        "stdout": result.stdout
                    }
                )
            
            # Get cherry-pick results
            cherry_pick_info = await self._get_cherry_pick_info(repository_path, commits)
            
            return SuccessResult(data={
                "message": f"Successfully cherry-picked commits",
                "repository_path": os.path.abspath(repository_path),
                "command": " ".join(cmd),
                "commits": commits,
                "cherry_pick_info": cherry_pick_info,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            return ErrorResult(
                message=f"Unexpected error during git cherry-pick: {str(e)}",
                code="UNEXPECTED_ERROR",
                details={"error": str(e)}
            )
    
    async def _get_cherry_pick_info(self, repo_path: str, commits: List[str]) -> Dict[str, Any]:
        """Get information about cherry-pick result."""
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
            
            # Get commit details for cherry-picked commits
            commit_details = []
            for commit in commits[:5]:  # Limit to first 5 commits for performance
                detail_result = subprocess.run(
                    ["git", "show", "--no-patch", "--format=fuller", commit],
                    capture_output=True,
                    text=True,
                    cwd=repo_path
                )
                
                if detail_result.returncode == 0:
                    commit_details.append({
                        "hash": commit,
                        "info": detail_result.stdout.strip()
                    })
            
            return {
                "current_branch": current_branch,
                "recent_commits": recent_commits,
                "commit_details": commit_details,
                "total_commits": len(commits)
            }
            
        except Exception:
            return {
                "current_branch": "",
                "recent_commits": [],
                "commit_details": [],
                "total_commits": len(commits)
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