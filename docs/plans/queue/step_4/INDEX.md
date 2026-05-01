# Step 4: Migrate Commands — Replace QueueManager Calls

## Goal
Rewrite every command that calls `QueueManager.add_*_task()` to instead
call `get_queue_integration().add_job(JobClass, job_id, params)`.

## Tactical Steps

| # | Task | Detail |
|---|------|---------|
| 4.1 | Migrate Docker commands (build/push/pull) | [TASKS.md](TASKS.md) + [4_all/INDEX.md](4_all/INDEX.md) |
| 4.2 | Migrate Git commands (clone/push/pull) | [TASKS.md](TASKS.md) |
| 4.3 | Migrate GitHub commands | [TASKS.md](TASKS.md) |
| 4.4 | Migrate K8s commands (deploy/pod/cluster/cert/mTLS) | [TASKS.md](TASKS.md) |
| 4.5 | Migrate Vast.ai commands (create/destroy/search/list) | [TASKS.md](TASKS.md) |
| 4.6 | Migrate FTP commands | [TASKS.md](TASKS.md) |
| 4.7 | Migrate Ollama commands (pull/run) | [TASKS.md](TASKS.md) |
| 4.8 | Migrate SSL commands (generate/view/verify/revoke) | [TASKS.md](TASKS.md) |
| 4.9 | Migrate System commands | [TASKS.md](TASKS.md) |
| 4.10 | Migrate queue management commands (`cancel` → `stop_job`, `remove` → `delete_job`) | [TASKS.md](TASKS.md) |

## Detailed Tasks
See: [TASKS.md](TASKS.md)

## Pattern Per Command
```python
# Before
qm = QueueManager()
task_id = qm.add_docker_push_task(image_name, tag)

# After
integration = get_queue_integration()
result = await integration.add_job(
    DockerJob,
    f"docker_push_{image_name}_{tag}",
    {"op": "push", "image_name": image_name, "tag": tag}
)
```

## Notes
- Discover real command file paths via `list_project_files(glob="**/commands/**")` first
- Complete dependency_matrix.md (Step 1.10) must be done before starting Step 4
- Migrate one domain at a time, update Status in matrix to DONE after each
- `job_id` must be deterministic: `f"{domain}_{operation}_{key_param}"`
- Return `job_id` from command so caller can poll status
