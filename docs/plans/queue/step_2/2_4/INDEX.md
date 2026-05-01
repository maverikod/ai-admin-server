# 2.4: Implement GitHubJob

## Atomic Steps
1. Read `GitHubExecutor` body
2. Create `ai_admin/jobs/github_job.py` with `class GitHubJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation_type"]` → create_repo/delete_repo/etc.
4. Port GitHub API calls (token auth, requests)
5. Port `user_roles` security validation
6. Add progress reporting
7. Docstring, type hints, lint + typecheck
