# 2.2 TASKS — Atomic Instructions for Haiku
## Subject: DockerJob

## TASK 1
**Action:** Read DockerExecutor file location
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="DockerExecutor"
)
```
**Save:** `exec_path` = entities[0]["file_path"] (make relative to project root)

## TASK 2
**Action:** Read DockerExecutor full body
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<exec_path>
)
```
**Extract:** push(), pull(), build() method bodies verbatim

## TASK 3
**Action:** Read add_push_task, add_pull_task, add_build_task from queue_manager_impl.py
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/task_queue/queue_manager/queue_manager_impl.py",
  start_line=30,
  end_line=200
)
```
**Extract:** params each method receives (image_name, tag, dockerfile_path, etc.)

## TASK 4
**Action:** Create docker_job.py via `cst_create_file` (NOT create_text_file — it does not support .py!)
```
cst_create_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py",
  docstring="DockerJob — queuemgr job for Docker build/push/pull operations."
)
```
**Save:** `tree_id` from response
**Note:** File is created with only the docstring. Class will be added in TASK 5.

## TASK 5
**Action:** Add DockerJob class to the tree
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "insert",
    "parent_node_id": "__root__",
    "position": "last",
    "code_lines": [
      "from queuemgr.jobs.base_core import QueueJobBase",
      "",
      "",
      "class DockerJob(QueueJobBase):",
      "    \\\"\\\"\\\"Execute Docker build/push/pull operations as a queue job.",
      "",
      "    Params keys:",
      "        op (str): 'build' | 'push' | 'pull'",
      "        image_name (str): Docker image name",
      "        tag (str): Image tag",
      "        dockerfile_path (str, optional): Path to Dockerfile (for build)",
      "        context_path (str, optional): Build context path (for build)",
      "    \\\"\\\"\\\"",
      "",
      "    def run(self) -> dict:",
      "        \\\"\\\"\\\"Execute the Docker operation.\\\"\\\"\\\"",
      "        op = self.params.get('op')",
      "        if op == 'push':",
      "            return self._push()",
      "        elif op == 'pull':",
      "            return self._pull()",
      "        elif op == 'build':",
      "            return self._build()",
      "        else:",
      "            raise ValueError(f'Unknown Docker op: {op}')",
      "",
      "    def _push(self) -> dict:",
      "        \\\"\\\"\\\"Push Docker image.\\\"\\\"\\\"",
      "        # PORT FROM: DockerExecutor.push()",
      "        raise NotImplementedError('Port from DockerExecutor.push()')",
      "",
      "    def _pull(self) -> dict:",
      "        \\\"\\\"\\\"Pull Docker image.\\\"\\\"\\\"",
      "        # PORT FROM: DockerExecutor.pull()",
      "        raise NotImplementedError('Port from DockerExecutor.pull()')",
      "",
      "    def _build(self) -> dict:",
      "        \\\"\\\"\\\"Build Docker image.\\\"\\\"\\\"",
      "        # PORT FROM: DockerExecutor.build()",
      "        raise NotImplementedError('Port from DockerExecutor.build()')"
    ]
  }]
)
```

## TASK 6
**Action:** Save tree to create file on disk
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py",
  backup=True,
  validate=True
)
```
**Expected:** success=True

## TASK 7
**Action:** Reload tree (file was just created, tree may be stale)
```
cst_load_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py"
)
```
**Save:** `tree_id` (new)

## TASK 8
**Action:** Find _push method node
```
cst_find_node(
  tree_id=<tree_id>,
  search_type="simple",
  node_type="FunctionDef",
  name="_push"
)
```
**Save:** `push_node_id`

## TASK 9
**Action:** Replace _push with real logic from DockerExecutor.push()
```
cst_modify_tree(
  tree_id=<tree_id>,
  operations=[{
    "action": "replace",
    "node_id": <push_node_id>,
    "code_lines": [
      "def _push(self) -> dict:",
      "    \\\"\\\"\\\"Push Docker image.\\\"\\\"\\\"",
      "    image_name = self.params['image_name']",
      "    tag = self.params['tag']",
      "    # <paste actual lines from DockerExecutor.push() body here>"
    ]
  }]
)
```
**Note to Haiku:** Copy the exact function body from TASK 2 output.

## TASK 10
**Action:** Same for _pull — find node, replace with DockerExecutor.pull() logic

## TASK 11
**Action:** Same for _build — find node, replace with DockerExecutor.build() logic

## TASK 12
**Action:** Save tree
```
cst_save_tree(
  tree_id=<tree_id>,
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py",
  backup=True,
  validate=True
)
```
**Expected:** success=True, no validation errors

## TASK 13
**Action:** Format code
```
format_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py"
)
```

## TASK 14
**Action:** Run lint
```
lint_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py"
)
```
**Expected:** error_count=0

## TASK 15
**Action:** Run type check
```
type_check_code(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="ai_admin/jobs/docker_job.py"
)
```
**Expected:** 0 mypy errors (or document known issues)

## DONE CHECK
- [ ] File created via cst_create_file (NOT create_text_file)
- [ ] DockerJob class added with run(), _push(), _pull(), _build()
- [ ] _push ported (no NotImplementedError)
- [ ] _pull ported
- [ ] _build ported
- [ ] format_code ran
- [ ] lint passes
- [ ] typecheck passes or issues documented
