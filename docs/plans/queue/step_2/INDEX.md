# Step 2: Define Job Classes — Create QueueJobBase Subclasses

## Goal
For every domain (Docker, Git, K8s, Vast.ai, FTP, Ollama, SSL, System)
create a `QueueJobBase` subclass that encapsulates execution logic now
scattered across Executor classes.

## Tactical Steps

| # | Task | Index | Tasks |
|---|------|-------|-------|
| 2.1 | Create `ai_admin/jobs/` package with `__init__.py` | [2_1/INDEX.md](2_1/INDEX.md) | [2_1/TASKS.md](2_1/TASKS.md) |
| 2.2 | Implement `DockerJob(QueueJobBase)` — build/push/pull | [2_2/INDEX.md](2_2/INDEX.md) | [2_2/TASKS.md](2_2/TASKS.md) |
| 2.3 | Implement `GitJob(QueueJobBase)` — clone/push/pull | [2_3/INDEX.md](2_3/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.4 | Implement `GitHubJob(QueueJobBase)` — repo ops | [2_4/INDEX.md](2_4/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.5 | Implement `K8sJob(QueueJobBase)` — deploy/pod/cluster/cert/mTLS | [2_5/INDEX.md](2_5/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.6 | Implement `VastJob(QueueJobBase)` — create/destroy/search/list | [2_6/INDEX.md](2_6/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.7 | Implement `FtpJob(QueueJobBase)` — merge FTPExecutor+FtpExecutor | [2_7/INDEX.md](2_7/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.8 | Implement `OllamaJob(QueueJobBase)` — pull/run | [2_8/INDEX.md](2_8/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.9 | Implement `SslJob(QueueJobBase)` — generate/view/verify/revoke | [2_9/INDEX.md](2_9/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |
| 2.10 | Implement `SystemJob(QueueJobBase)` — system_monitor | [2_10/INDEX.md](2_10/INDEX.md) | [2_3_to_2_10/TASKS.md](2_3_to_2_10/TASKS.md) |

## Notes
- **Use `cst_create_file` (NOT `create_text_file`) for all `.py` files**
- Each Job class receives params dict, executes via `run()`, reports progress
- Job params mirror the current `add_*_task()` signatures from `QueueManager`
- No changes to commands yet — Jobs are pure logic units
- Read FTP diff (step_1/ftp_executor_diff.md) before implementing 2.7
- Read QueueManager diff (step_1/queuemanager_diff.md) for context on duplicate before 2.x
