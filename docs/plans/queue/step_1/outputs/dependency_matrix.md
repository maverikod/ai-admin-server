# Step 1.10 — Dependency matrix (master migration checklist)

## Scope and paths

- **Artifacts:** Step 1.1–1.9 audit outputs live under `docs/plans/queue/step_1/outputs/` (nine markdown files). This document merges those findings with `1_10/TASKS.md`, `1_10/INDEX.md`, and **Step 1.10** in `docs/plans/queue/PARALLEL.md` (1.10 depends on 1.1–1.9 and 1.4).
- **Paths vs. INDEX examples:** `1_10/INDEX.md` shows an example row using `VastExecutor` and `create()`. **Repo dispatch uses `MiscExecutor`** (and `TaskQueueCore` helpers such as `_execute_ssh_task`), not a separate `VastExecutor` class — see `outputs/executors_map.md` and `outputs/task_executor_map.md`. Older `TASKS.md` paths under `docs/plans/step_1/` are superseded by `docs/plans/queue/step_1/outputs/`.

---

## Table A — `add_*` method → target Job class (Step 2)

| add_method / entry | Target Job class |
|--------------------|------------------|
| `add_push_task`, `add_pull_task`, `add_build_task` | DockerJob |
| `add_git_task` | GitJob |
| `add_github_task` | GitHubJob |
| `add_k8s_deployment_create_task`, `add_k8s_pod_create_task`, `add_k8s_cluster_create_task`, `add_k8s_certificate_create_task`, `add_k8s_mtls_setup_task` | K8sJob |
| `add_vast_create_task`, `add_vast_destroy_task`, `add_vast_search_task`, `add_vast_instances_task` | VastJob |
| `add_ollama_pull_task`, `add_ollama_run_task` | OllamaJob |
| `add_ssl_task` | SslJob |
| `add_system_task` | SystemJob |
| `add_task` | Depends on `task.task_type` / caller |
| `push_task` | CUSTOM_SCRIPT path → treat with custom/script migration |

---

## Table B — Command modules × QueueManager / legacy queue API

Sources: `outputs/queuemanager_importers.md` and spot-check under `ai_admin/commands/*.py` (no claim of exhaustive scan beyond importer list + queue-related commands).

| Command module (primary) | Command class | Manager / facade | Queue API used (observed) |
|----------------------------|---------------|------------------|---------------------------|
| `ai_admin/task_queue/__init__.py` | (re-export) | — | re-export `QueueManager` |
| `ai_admin/queue_management/queue_client.py` | `QueueClient` | `QueueManager()` | see **Table C** |
| `ai_admin/commands/queue_cancel_task_command.py` | (cancel) | `QueueManager()` | `get_task`, `cancel_task`, `get_task` |
| `ai_admin/commands/queue_remove_task_command.py` | (remove) | `QueueManager()` | `get_task`, `remove_task` |
| `ai_admin/commands/vast_create_command.py` | `VastCreateCommand` | `QueueManager()` | `add_task` ( `TaskType.VAST_CREATE` ), `get_tasks_by_status` |
| `ai_admin/commands/vast_destroy_command.py` | `VastDestroyCommand` | `QueueManager()` | `add_task` ( `TaskType.VAST_DESTROY` ), `get_tasks_by_status` |
| `ai_admin/commands/docker_pull_command.py` | `DockerPullCommand` | `TaskQueueManager()` | `add_task` (mixed / legacy imports) |
| `ai_admin/commands/ftp_upload_command.py` | (FTP) | `queue_manager` singleton | `add_task` |
| `ai_admin/commands/ftp_info_command.py` | (FTP) | `queue_manager` singleton | `add_task` |
| `ai_admin/commands/ftp_rename_command.py` | (FTP) | `queue_manager` singleton | `add_task` |
| `ai_admin/commands/ftp_mkdir_command.py` | (FTP) | `queue_manager` singleton | `add_task` |
| `ai_admin/commands/ftp_list_command.py` | (FTP) | `TaskQueueManager()` | `add_task` |
| `ai_admin/commands/ftp_download_command.py` | (FTP) | `TaskQueueManager()` | `add_task` |
| `ai_admin/commands/ftp_delete_command.py` | (FTP) | `TaskQueueManager()` | `add_task` |
| `ai_admin/commands/ssh_exec_command.py` | `SshExecCommand` | `queue_manager` singleton | `add_task` ( `TaskType.SSH_EXEC` ) |

**Importer summary note:** `queuemanager_importers.md` groups several FTP files as `ftp_*` and names `dynamic queue_manager` / `TaskQueueManager` patterns; this table expands concrete modules verified in-repo.

---

## Table C — `QueueClient` public commands → `QueueManager` calls

Defined in `ai_admin/queue_management/queue_client.py`. Importers: `outputs/queueclient_importers.md`.

| QueueClient method | Underlying `QueueManager` / behavior |
|--------------------|--------------------------------------|
| `get_queue_status` | `get_queue_status`, `list_tasks`, optional filter, `_calculate_metrics` |
| `get_task_status` | `get_task` |
| `get_task_logs` | `get_task_logs` |
| `manage_task` | `pause_task` / `resume_task` / `retry_task` / `cancel_task` / `set_task_priority` / `move_task` (by `QueueAction`) |
| `clear_queue` | `list_tasks`, loop `remove_task` per matching task |
| `get_queue_health` | `list_tasks`, `_calculate_metrics` |
| `get_queue_statistics` | `list_tasks`, optional time filter |

Consumers (commands): `queue_health_command`, `queue_statistics_command`, `queue_logs_command`, `queue_filter_command`, `queue_clear_command` (+ mirrored `commands/` tree per 1.2).

---

## Table D — Full `add_*` / enqueue catalogue (`task_executor_map`)

From `outputs/task_executor_map.md` — **implementing class** names match `TaskQueueCore._execute_task` / nested executors (`DockerExecutor`, `K8sKindExecutor`, `OllamaExecutor`, `MiscExecutor`, `FTPExecutor` for FTP branches). **Vast / Git / GitHub / several K8s enqueue helpers** route to **`MiscExecutor._execute_generic_task`** in the dispatch table (see Blockers).

| add_method | TaskType (value) | Dispatch helper | Implementing class | executor_method |
|------------|------------------|-----------------|--------------------|-----------------|
| `add_push_task` | DOCKER_PUSH (`docker_push`) | `_execute_docker_push_task` | DockerExecutor | `_execute_docker_push_task` |
| `add_git_task` | GIT_OPERATION (`git_operation`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_github_task` | GITHUB_OPERATION (`github_operation`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_build_task` | DOCKER_BUILD (`docker_build`) | `_execute_docker_build_task` | DockerExecutor | `_execute_docker_build_task` |
| `add_pull_task` | DOCKER_PULL (`docker_pull`) | `_execute_docker_pull_task` | DockerExecutor | `_execute_docker_pull_task` |
| `add_ollama_pull_task` | OLLAMA_PULL (`ollama_pull`) | `_execute_ollama_pull_task` | OllamaExecutor | `_execute_ollama_pull_task` |
| `add_ollama_run_task` | OLLAMA_RUN (`ollama_run`) | `_execute_ollama_run_task` | OllamaExecutor | `_execute_ollama_run_task` |
| `add_k8s_deployment_create_task` | K8S_DEPLOYMENT_CREATE (`k8s_deployment_create`) | `_execute_k8s_deployment_create_task` | K8sKindExecutor | `_execute_k8s_deployment_create_task` |
| `add_k8s_pod_create_task` | K8S_POD_CREATE (`k8s_pod_create`) | `_execute_k8s_pod_create_task` | K8sKindExecutor | `_execute_k8s_pod_create_task` |
| `add_k8s_cluster_create_task` | K8S_CLUSTER_CREATE (`k8s_cluster_create`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_k8s_certificate_create_task` | K8S_CERTIFICATE_CREATE (`k8s_certificate_create`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_k8s_mtls_setup_task` | K8S_MTLS_SETUP (`k8s_mtls_setup`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_vast_create_task` | VAST_CREATE (`vast_create`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_vast_destroy_task` | VAST_DESTROY (`vast_destroy`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_vast_search_task` | VAST_SEARCH (`vast_search`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_vast_instances_task` | VAST_INSTANCES (`vast_instances`) | generic | MiscExecutor | `_execute_generic_task` |
| `add_system_task` | SYSTEM_MONITOR (`system_monitor`) | `_execute_system_monitor_task` | MiscExecutor | `_execute_system_monitor_task` |
| `add_task` | (caller-defined) | per `task.task_type` | (branch-specific) | (branch-specific) |
| `add_ssl_task` | SSL_OPERATION (`ssl_operation`) | `_execute_ssl_operation_task` | MiscExecutor | `_execute_ssl_operation_task` |
| `push_task` | CUSTOM_SCRIPT (`custom_script`) | `_execute_custom_script_task` | MiscExecutor | `_execute_custom_script_task` |

---

## Auxiliary facts (merged from Step 1.1–1.9 outputs)

- **Canonical `QueueManager`:** `ai_admin/task_queue/queue_manager/queue_manager_impl.py`; duplicate root `queue_manager.py` adds module singleton `queue_manager` (see `queuemanager_diff.md`).
- **Executors:** No standalone `GitExecutor`, `GitHubExecutor`, `VastExecutor`, `SSLExecutor`, `SystemExecutor` — grouping under **`MiscExecutor`** plus domain executors (`DockerExecutor`, `K8sKindExecutor`, `OllamaExecutor`, FTP types); see `executors_map.md`.
- **FTP:** Two classes / paths (`FTPExecutor` vs `FtpExecutor`); merge strategy draft in `ftp_executor_diff.md`.
- **TaskStatus:** Duplicate definitions (`task_status.py` vs `enums.py`); `queuemgr` / `JobStatus` mapping still TODO in `task_status_map.md`.
- **QueueAction / QueueFilter:** enums and usages in `queue_action_filter_map.md`.
- **QueueDaemon:** no Python class found in snapshot — `queue_daemon_analysis.md`; clarify before any Step 6.7 delete.

---

## Blockers (numbered)

1. **`MiscExecutor._execute_generic_task` vs `_execute_task` else branch** — Types routed to generic (Git, GitHub, several K8s, all Vast) hit code that only accepts `custom_script` / `custom_command`; other `task_type` values fail at runtime (see `task_executor_map.md` blockers + citations).
2. **`add_github_task` import inconsistency** — Mixed `Task` / `TaskType` import paths in `queue_manager_impl.py` (`task_executor_map.md`).
3. **`max_concurrent` facade vs `TaskQueueCore`** — `QueueManager` sets `TaskQueue.max_concurrent`; scheduler reads `TaskQueueCore.max_concurrent` (`task_executor_map.md`).
4. **`TaskQueue` façade attributes** — References to `self.dockerExecutor` / etc. never assigned; verify live path vs dead methods (`executors_map.md`).
5. **`queuemgr` JobStatus** — Install/locate package and map (`task_status_map.md`).
6. **`QueueDaemon` scope** — Absent in sources; do not assume Step 6.7 target until clarified (`queue_daemon_analysis.md`).
7. **Design doc vs repo names** — Replace any remaining `VastExecutor`-style names with **`MiscExecutor`** / actual dispatch (`_execute_generic_task`, dedicated `_execute_*` branches) when updating migration docs.

---

## Done checklist (Step 1.10)

- [ ] Every row from `queuemanager_importers.md` is reflected in **Table B** (and expanded FTP lines).
- [ ] Every `add_method` in **Table D** has executor + TaskType + dispatch column populated from `task_executor_map.md`.
- [ ] Migration status column (TODO / IN PROGRESS / DONE) tracked per-row during Step 4+ (currently not repeated here — use project tracker or extend this file).
- [ ] Test coverage column (YES / NO) updated when Step 5 tests land.
- [ ] Executor naming aligned with **Table D** / `task_executor_map` (**`MiscExecutor`**, not fictional `VastExecutor`).
- [ ] File indexed under Step 1 output artifacts (`INDEX.md`).

---

## Summary counts

| Item | Count |
|------|-------|
| Source audit files merged (Step 1 outputs) | 9 (`*.md` in `outputs/`, excluding this file) |
| Rows in **Table B** (command × API) | 14 data rows (+ sub-rows implied by grouped FTP in 1.1) |
| Rows in **Table D** (`add_*` / `push_task` catalogue) | 20 |
| `QueueClient` public methods in **Table C** | 7 |
| **Table A** mapping groups | 10 |

---

## Parallel plan reference (Step 1.10)

From `PARALLEL.md`: substeps 1.1–1.9 may run in parallel; **1.4** maps `add_*` → executor after 1.1 + 1.3; **1.10** runs after **1.1–1.9 all**. Dependency matrix gates Step 2+ (`1.10 blocks 2+3` constraint table).
