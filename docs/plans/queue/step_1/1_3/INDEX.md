# 1.3: List All Executor Classes and Their Methods

## Atomic Steps
1. Run `list_code_entities(entity_type="class", file_path="ai_admin/task_queue")` — get all Executor classes
2. For each Executor class run `list_class_methods(class_name=...)`
3. Build table: Executor → methods → what subprocess/API it calls
4. Note `DockerExecutor`, `K8sExecutor`, `K8sKindExecutor`, `KindExecutor`, `FTPExecutor`, `FtpExecutor`, `VastExecutor`, `OllamaExecutor`, `GitExecutor`, `GitHubExecutor`, `SSLExecutor`, `SystemExecutor`
5. Save to `docs/plans/step_1/executors_map.md`
