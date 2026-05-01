# 2.2: Implement DockerJob

## Atomic Steps
1. Read `DockerExecutor` body to extract all execution logic
2. Create `ai_admin/jobs/docker_job.py` with `class DockerJob(QueueJobBase)`
3. Implement `run(self)`: dispatch by `self.params["op"]` → push/pull/build
4. Port subprocess calls from `DockerExecutor.push()`, `.pull()`, `.build()` verbatim
5. Add progress reporting: `self.update_progress(pct, message)` at key checkpoints
6. Add error handling: catch subprocess errors, set job failed with message
7. Add docstring and type hints to class and `run()`
8. Run `lint_code` + `type_check_code` on the file
