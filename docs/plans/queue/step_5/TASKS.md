# STEP 5 TASKS — Atomic Instructions for Haiku
# Tests: cover new Job classes and migrated commands

## CRITICAL: Test file creation
**Test files are `.py` — use `cst_create_file` (NOT `create_text_file`).**
Pattern:
```
1. cst_create_file(project_id, file_path="tests/queue/test_X.py", docstring="...")  → tree_id
2. cst_modify_tree(tree_id, insert imports + test class code at __root__)  → in-memory
3. cst_save_tree(tree_id, project_id, file_path, backup=False, validate=True)  → disk
```
**Note:** `backup=False` for test files is acceptable (no production code at risk).

---

## 5.1–5.5: Unit Tests Per Job Class
### Pattern (repeat for each Job class):

**Variables to fill:**
```
JOB_CLASS   = "DockerJob"               # change per domain
TEST_FILE   = "tests/queue/test_docker_job.py"
MOCK_TARGET = "subprocess.run"          # import path mocked inside _push/_pull/_build
```

### TASK A: Discover real mock target
Read the Job file to find the exact import used for subprocess/API:
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py"
)
```
Find the `import subprocess` or `from X import Y` line.
**Save:** `MOCK_TARGET` = exact dotted path, e.g. `"ai_admin.jobs.docker_job.subprocess.run"`

### TASK B: Create test file
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_docker_job.py",
  docstring="Unit tests for DockerJob."
)
```
Save: `tree_id`

### TASK C: Add imports and test classes
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": [
      "from unittest.mock import patch, MagicMock",
      "import pytest",
      "from ai_admin.jobs.docker_job import DockerJob",
      "",
      "",
      "class TestDockerJobPush:",
      "    \\\"\\\"\\\"Tests for DockerJob push operation.\\\"\\\"\\\"",
      "",
      "    def test_push_success(self):",
      "        \\\"\\\"\\\"Test successful Docker push.\\\"\\\"\\\"",
      "        job = DockerJob(params={'op': 'push', 'image_name': 'myapp', 'tag': 'v1.0'})",
      "        with patch('<MOCK_TARGET>') as mock_run:",
      "            mock_run.return_value = MagicMock(returncode=0, stdout='pushed', stderr='')",
      "            result = job.run()",
      "        assert result['success'] is True",
      "",
      "    def test_push_failure(self):",
      "        \\\"\\\"\\\"Test Docker push failure handling.\\\"\\\"\\\"",
      "        job = DockerJob(params={'op': 'push', 'image_name': 'myapp', 'tag': 'v1.0'})",
      "        with patch('<MOCK_TARGET>') as mock_run:",
      "            mock_run.return_value = MagicMock(returncode=1, stdout='', stderr='denied')",
      "            result = job.run()",
      "        assert result['success'] is False",
      "        assert 'denied' in result.get('error', '')",
      "",
      "",
      "class TestDockerJobUnknownOp:",
      "    \\\"\\\"\\\"Tests for unknown operation handling.\\\"\\\"\\\"",
      "",
      "    def test_unknown_op_raises(self):",
      "        \\\"\\\"\\\"Test that unknown op raises ValueError.\\\"\\\"\\\"",
      "        job = DockerJob(params={'op': 'invalid'})",
      "        with pytest.raises(ValueError):",
      "            job.run()"
    ]
  }]
)
```
**Note:** Replace `<MOCK_TARGET>` with the real path from TASK A.

### TASK D: Save test file
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_docker_job.py",
  backup=False,
  validate=True
)
```

### TASK E: Run tests
```
run_project_module(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  module="pytest",
  args=["tests/queue/test_docker_job.py", "-v", "--tb=short"]
)
```
Read output. If failures:
- Wrong mock path → reload tree, fix MOCK_TARGET string, save, re-run
- Import error → check Job file was saved correctly in Step 2

### TASK F: Lint test file
```
lint_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_docker_job.py"
)
```
**Expected:** error_count=0

---

## Repeat TASKS A–F for each Job:

| Step | Test file | Job class | Mock target |
|------|-----------|-----------|-------------|
| 5.1 | test_docker_job.py | DockerJob | subprocess.run |
| 5.2 (Git) | test_git_job.py | GitJob | subprocess.run, ops: clone/push/pull |
| 5.2 (GitHub) | test_github_job.py | GitHubJob | requests.post / requests.get |
| 5.3 | test_k8s_job.py | K8sJob | subprocess.run (kubectl/kind), 5 ops |
| 5.4 | test_vast_job.py | VastJob | requests session, 4 ops |
| 5.5 (FTP) | test_ftp_job.py | FtpJob | ftplib.FTP |
| 5.5 (Ollama) | test_ollama_job.py | OllamaJob | OllamaClient |
| 5.5 (SSL) | test_ssl_job.py | SslJob | subprocess (openssl) |
| 5.5 (System) | test_system_job.py | SystemJob | psutil |

---

## 5.6: Integration test — Queue lifecycle

### TASK 1: Create test file
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_integration_lifecycle.py",
  docstring="Integration tests for QueueManagerIntegration lifecycle."
)
```
Save: tree_id

### TASK 2: Add test code
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": [
      "import asyncio",
      "import pytest",
      "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
      "from ai_admin.jobs.system_job import SystemJob",
      "",
      "",
      "@pytest.mark.asyncio",
      "async def test_job_lifecycle_pending_to_completed():",
      "    \\\"\\\"\\\"Test full job lifecycle: add \u2192 run \u2192 complete.\\\"\\\"\\\"",
      "    q = QueueManagerIntegration(in_memory=True, max_concurrent_jobs=1)",
      "    await q.start()",
      "    try:",
      "        result = await q.add_job(SystemJob, 'test_lifecycle_1', {",
      "            'operation_type': 'system_monitor',",
      "            'include_gpu': False,",
      "            'include_temperature': False,",
      "            'include_processes': False,",
      "        })",
      "        assert result.job_id == 'test_lifecycle_1'",
      "        for _ in range(20):",
      "            status = await q.get_job_status('test_lifecycle_1')",
      "            if status.status in ('completed', 'failed'):",
      "                break",
      "            await asyncio.sleep(0.5)",
      "        assert status.status == 'completed'",
      "    finally:",
      "        await q.stop()"
    ]
  }]
)
```

### TASK 3: Save
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_integration_lifecycle.py",
  backup=False,
  validate=True
)
```

### TASK 4: Run
```
run_project_module(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  module="pytest",
  args=["tests/queue/test_integration_lifecycle.py", "-v", "--tb=long"]
)
```
Expected: all tests pass.

---

## 5.7: Integration test — Command → queue

### TASK 1: Discover real command file path
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="**/vast_create_command.py"
)
```
Save: exact relative path (use this in test patch string)

### TASK 2: Create test file (cst_create_file pattern)
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_command_integration.py",
  docstring="Integration tests: command submits correct job to queue."
)
```

### TASK 3: Add test code (adapt patch path to real command module path)
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": [
      "from unittest.mock import AsyncMock, patch, MagicMock",
      "import pytest",
      "from ai_admin.jobs.vast_job import VastJob",
      "",
      "",
      "@pytest.mark.asyncio",
      "async def test_vast_create_command_submits_job():",
      "    \\\"\\\"\\\"Test VastCreateCommand submits VastJob to queue.\\\"\\\"\\\"",
      "    from ai_admin.commands.vast_create_command import VastCreateCommand",
      "    mock_integration = AsyncMock()",
      "    mock_integration.add_job.return_value = MagicMock(job_id='vast_test_1', status='pending')",
      "    with patch('ai_admin.commands.vast_create_command.get_queue_integration',",
      "               return_value=mock_integration):",
      "        cmd = VastCreateCommand()",
      "        result = await cmd.execute(",
      "            project_id='c86dded6-6f93-4fb0-be54-b6d7b739eeb9',",
      "            bundle_id=12345, image='ubuntu:22.04', disk=10.0",
      "        )",
      "    mock_integration.add_job.assert_called_once()",
      "    call_args = mock_integration.add_job.call_args",
      "    assert call_args[0][0] == VastJob",
      "    assert call_args[0][2]['operation'] == 'create'",
      "    assert call_args[0][2]['bundle_id'] == 12345",
      "    assert result.data['job_id'] == 'vast_test_1'"
    ]
  }]
)
```

### TASK 4: Save + run
```
cst_save_tree(tree_id, project_id, file_path, backup=False, validate=True)
run_project_module(project_id, module="pytest",
  args=["tests/queue/test_command_integration.py", "-v"])
```

---

## 5.8: Test queue size limits

### TASK 1: Create test file (cst_create_file pattern)
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_queue_limits.py",
  docstring="Tests for queue size and per-type limits."
)
```

### TASK 2: Add test code
```
cst_modify_tree(tree_id, operations=[{"insert __root__ last": [
  "import asyncio",
  "import pytest",
  "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
  "from ai_admin.jobs.system_job import SystemJob",
  "",
  "",
  "@pytest.mark.asyncio",
  "async def test_max_queue_size_eviction():",
  "    q = QueueManagerIntegration(in_memory=True, max_concurrent_jobs=0, max_queue_size=2)",
  "    await q.start()",
  "    try:",
  "        params = {'operation_type': 'system_monitor', 'include_gpu': False,",
  "                  'include_temperature': False, 'include_processes': False}",
  "        await q.add_job(SystemJob, 'job_1', params)",
  "        await q.add_job(SystemJob, 'job_2', params)",
  "        await q.add_job(SystemJob, 'job_3', params)  # evicts job_1",
  "        jobs = await q.list_jobs()",
  "        job_ids = [j.job_id for j in jobs]",
  "        assert 'job_1' not in job_ids",
  "        assert 'job_2' in job_ids",
  "        assert 'job_3' in job_ids",
  "    finally:",
  "        await q.stop()"
]}])
```

### TASK 3: Save + run
```
cst_save_tree(...) + run_project_module(module="pytest",
  args=["tests/queue/test_queue_limits.py", "-v"])
```

---

## 5.9: Test completed job retention (TTL)

### TASK 1: Create test file (cst_create_file pattern)
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="tests/queue/test_queue_cleanup.py",
  docstring="Tests for completed job retention and cleanup."
)
```

### TASK 2: Add test code
```
cst_modify_tree(tree_id, operations=[{"insert __root__ last": [
  "import asyncio, pytest",
  "from mcp_proxy_adapter.queue.integration import QueueManagerIntegration",
  "from ai_admin.jobs.system_job import SystemJob",
  "",
  "",
  "@pytest.mark.asyncio",
  "async def test_completed_job_cleaned_up_after_retention():",
  "    q = QueueManagerIntegration(in_memory=True, max_concurrent_jobs=1,",
  "                                completed_job_retention_seconds=1)",
  "    await q.start()",
  "    try:",
  "        await q.add_job(SystemJob, 'cleanup_1', {",
  "            'operation_type': 'system_monitor', 'include_gpu': False,",
  "            'include_temperature': False, 'include_processes': False})",
  "        for _ in range(20):",
  "            s = await q.get_job_status('cleanup_1')",
  "            if s.status == 'completed': break",
  "            await asyncio.sleep(0.3)",
  "        await asyncio.sleep(3)  # wait retention + cleanup cycle",
  "        jobs = await q.list_jobs()",
  "        assert 'cleanup_1' not in [j.job_id for j in jobs]",
  "    finally:",
  "        await q.stop()"
]}])
```

### TASK 3: Save + run
```
cst_save_tree(...) + run_project_module(module="pytest",
  args=["tests/queue/test_queue_cleanup.py", "-v", "-s"])
```

---

## 5.10: Final comprehensive_analysis

### TASK 1
```
comprehensive_analysis(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  check_placeholders=True,
  check_stubs=True,
  check_empty_methods=True,
  check_imports=True,
  check_long_files=True,
  check_flake8=True,
  check_mypy=True
)
```
This is queued. Save job_id. Poll `queue_get_job_status` until status=="completed".

### TASK 2: Read summary
Check:
- `total_stubs` in production code = 0
- No file in `ai_admin/jobs/` or `ai_admin/commands/` exceeds 400 lines
- `flake8_errors` in `ai_admin/` = 0

### TASK 3: Gate check
If all checks pass → proceed to Step 6 (Delete legacy layer).
If any fail → fix issues, re-run comprehensive_analysis, do NOT proceed to Step 6.

## DONE CHECK for Step 5
- [ ] 9 unit test files created and passing
- [ ] Integration lifecycle tests: passing
- [ ] Command integration tests: passing
- [ ] Queue size limit tests: passing
- [ ] Cleanup/TTL tests: passing
- [ ] comprehensive_analysis: 0 stubs in production code
- [ ] All flake8 errors in ai_admin/ = 0
- [ ] Gate to Step 6 cleared
