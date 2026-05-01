# Step 4 Atomic Steps: Migrate Commands

## 4.1: Docker Commands
1. Read `DockerBuildCommand`, `DockerPushCommand`, `DockerPullCommand` via `universal_file_read`
2. For each: identify `QueueManager().add_*_task(...)` call
3. Replace with `get_queue_integration().add_job(DockerJob, job_id, params_dict)`
4. Remove `from ai_admin.task_queue.queue_manager import QueueManager` import
5. Add `from ai_admin.queue import get_queue_integration` and `from ai_admin.jobs import DockerJob`
6. Apply via `cst_modify_tree` (preview first)
7. Lint + typecheck

## 4.2–4.9: Same pattern for each domain
- Git: `GitCloneCommand`, `GitPushCommand`, `GitPullCommand` → `GitJob`
- GitHub: all GitHub commands → `GitHubJob`
- K8s: 5 commands → `K8sJob`
- Vast.ai: 4 commands → `VastJob`
- FTP: FTP commands → `FtpJob`
- Ollama: `OllamaPullCommand`, `OllamaRunCommand` → `OllamaJob`
- SSL: 4 commands → `SslJob`
- System: `SystemMonitorCommand` → `SystemJob`

## 4.10: Queue Management Commands
1. Read `QueueCancelTaskCommand` → replace `qm.cancel_task(task_id)` with `integration.stop_job(task_id)`
2. Read `QueueRemoveTaskCommand` → replace `qm.remove_task(task_id)` with `integration.delete_job(task_id)`
3. Update response format: old `{task_id, status}` → new `QueueJobResult` fields
4. Apply via CST, lint + typecheck

## Checklist Per Command
- [ ] Remove QueueManager import
- [ ] Add get_queue_integration import
- [ ] Add Job class import
- [ ] Build params dict (same keys as old add_*_task signature)
- [ ] Generate deterministic job_id string
- [ ] Await add_job and return job_id in response
- [ ] Lint + typecheck passes
