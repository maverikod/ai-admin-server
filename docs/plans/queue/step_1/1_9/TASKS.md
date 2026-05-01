# 1.9 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Find QueueDaemon class
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="QueueDaemon"
)
```
**Save:** `daemon_entity` = entities[0] (file_path, line)

## TASK 2
**Action:** Get QueueDaemon methods
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="QueueDaemon"
)
```
**Save:** `daemon_methods`

## TASK 3
**Action:** Find all usages of QueueDaemon (instantiation sites)
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="QueueDaemon",
  target_type="class"
)
```
**Filter:** usage_type == "instantiation" or "import"

## TASK 4
**Action:** Search for QueueDaemon in scripts
```
fulltext_search(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  query="QueueDaemon"
)
```
**Note:** any hit in scripts/ is a CLI entry point

## TASK 5
**Action:** Read QueueDaemon._daemon_loop body
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<daemon_entity["file_path"] relative>,
  start_line=<_daemon_loop method line>,
  end_line=<_daemon_loop method line + 30>
)
```
**Question to answer:** does _daemon_loop manage jobs or just keep process alive?

## TASK 6
**Action:** Compare QueueDaemon.start() vs QueueManagerIntegration.start()
Read QueueDaemon.start() body (5-10 lines from method line)
**Question:** does QueueDaemon.start() do anything QueueManagerIntegration.start() does not?

## TASK 7
**Action:** Build analysis report:
```
## QueueDaemon Analysis
- File: {path}
- Methods: {list}
- Instantiation sites: {list of files}
- CLI entry points: {list or NONE}
- _daemon_loop purpose: {description}
- Superseded by QueueManagerIntegration: YES/PARTIALLY/NO
- Unique logic to preserve: {list or NONE}
- Deletion plan: Step 5.6
```

## TASK 8
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queue_daemon_analysis.md",
  content=<report>
)
```

## DONE CHECK
- [ ] file_path found
- [ ] All instantiation sites listed
- [ ] CLI entry points checked
- [ ] Superseded? answered
- [ ] Unique logic catalogued or confirmed NONE
