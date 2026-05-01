# 2.1 TASKS — Atomic Instructions for Haiku

## CRITICAL: Use `cst_create_file` for .py files, NOT `create_text_file`

## TASK 1
**Action:** Check if `ai_admin/jobs/` already exists
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/jobs/*"
)
```
**If count > 0:** skip TASK 2–4, go to TASK 5.

## TASK 2
**Action:** Verify `queuemgr.jobs.base_core.QueueJobBase` is importable
```
run_project_module(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  module="python",
  args=["-c", "from queuemgr.jobs.base_core import QueueJobBase; print('OK')"]
)
```
**Expected output:** `OK`
**If error:** run Step 3.1 first (install queuemgr), then return here.

## TASK 3
**Action:** Create `ai_admin/jobs/__init__.py` via `cst_create_file`
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/__init__.py",
  docstring="Job classes for queuemgr-based task execution."
)
```
**Save:** `tree_id`
**Note:** File created with only docstring. Imports added in TASK 4.

## TASK 4
**Action:** Add Job class imports to `__init__.py`
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": [
      "from .docker_job import DockerJob",
      "from .git_job import GitJob",
      "from .github_job import GitHubJob",
      "from .k8s_job import K8sJob",
      "from .vast_job import VastJob",
      "from .ftp_job import FtpJob",
      "from .ollama_job import OllamaJob",
      "from .ssl_job import SslJob",
      "from .system_job import SystemJob",
      "",
      "__all__ = [",
      "    'DockerJob', 'GitJob', 'GitHubJob', 'K8sJob',",
      "    'VastJob', 'FtpJob', 'OllamaJob', 'SslJob', 'SystemJob',",
      "]"
    ]
  }]
)
```
**Note:** These imports will fail until all Job files are created (Steps 2.2–2.10).
That is expected. The file is a placeholder until all Jobs exist.

## TASK 5
**Action:** Save `__init__.py`
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/__init__.py",
  backup=False,
  validate=False
)
```
**Note:** `validate=False` here because sibling Job modules don't exist yet
(imports will fail validation). Set `validate=True` only after all Job files created.

## TASK 6
**Action:** Get queuemgr version for requirements.txt
```
project_pip_show(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  packages=["queuemgr"]
)
```
**Save:** version string.

## TASK 7
**Action:** Verify `ai_admin/jobs/__init__.py` is indexed
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="ai_admin/jobs/__init__.py"
)
```
**Expected:** count=1

## DONE CHECK
- [ ] ai_admin/jobs/__init__.py created via `cst_create_file` (NOT create_text_file)
- [ ] QueueJobBase import verified working
- [ ] queuemgr version noted for requirements.txt
- [ ] File indexed (count=1 in list_project_files)
