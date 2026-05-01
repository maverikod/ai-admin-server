# 1.4: Map Each add_*_task Method to Its Executor

## Atomic Steps
1. Read `QueueManager.add_*_task()` bodies via `universal_file_read` on `queue_manager_impl.py`
2. For each method identify which Executor class it instantiates and which method it calls
3. Build mapping table:
   `add_push_task` → `DockerExecutor.push()`
   `add_git_task` → `GitExecutor.execute()`
   etc.
4. Flag any `add_*_task` with no corresponding Executor (direct inline logic)
5. Save to `docs/plans/step_1/task_executor_map.md`
