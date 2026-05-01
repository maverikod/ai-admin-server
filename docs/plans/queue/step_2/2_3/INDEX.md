# 2.3: Implement GitJob

## Atomic Steps
1. Read `GitExecutor` body
2. Create `ai_admin/jobs/git_job.py` with `class GitJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation_type"]` → clone/push/pull
4. Port SSL config handling from `GitExecutor`
5. Port `user_roles` security validation call
6. Add progress at: repo contact, transfer, checkout
7. Add docstring, type hints, lint + typecheck
