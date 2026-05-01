# 2.6: Implement VastJob

## Atomic Steps
1. Read `VastExecutor` body
2. Create `ai_admin/jobs/vast_job.py` with `class VastJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation"]` → create/destroy/search/list
4. Port Vast.ai API calls (bundle_id, image, disk, env_vars, label, onstart)
5. Port `user_roles` security validation
6. Add progress reporting for long create/destroy operations
7. Docstring, type hints, lint + typecheck
