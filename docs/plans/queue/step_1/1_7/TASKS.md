# 1.7 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Find TaskStatus class definition
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="TaskStatus"
)
```
**Save:** `ts_entity` = entities[0], note file_path and line

## TASK 2
**Action:** Read TaskStatus class body (5 lines from its line)
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative path from ts_entity>,
  start_line=<ts_entity["line"]>,
  end_line=<ts_entity["line"] + 20>
)
```
**Extract:** all enum value names (e.g. PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)
**Save:** `status_values` = ["PENDING", "RUNNING", ...]

## TASK 3
**Action:** Search for each status value usage
For each value in `status_values`:
```
fulltext_search(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  query="TaskStatus.{VALUE}"
)
```
**Save:** dict `{value: [file_path list]}`

## TASK 4
**Action:** Find queuemgr JobStatus values
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=".venv/lib/python3.12/site-packages/queuemgr/jobs/base_core.py",
  start_line=1,
  end_line=30
)
```
**Extract:** queuemgr status enum values

## TASK 5
**Action:** Build translation table
```
| TaskStatus (old) | queuemgr JobStatus (new) | notes |
|------------------|--------------------------|-------|
| PENDING          | pending                  |       |
| RUNNING          | running                  |       |
| COMPLETED        | completed                |       |
| FAILED           | failed                   |       |
| CANCELLED        | stopped                  | closest match |
```

## TASK 6
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/task_status_map.md",
  content=<table>
)
```

## DONE CHECK
- [ ] All TaskStatus values listed
- [ ] All usages found per value
- [ ] queuemgr equivalents mapped
- [ ] Any unmapped status flagged with TODO
