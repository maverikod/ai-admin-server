# 1.8 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Find QueueAction class
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="QueueAction"
)
```
**Save:** file_path and line

## TASK 2
**Action:** Read QueueAction body
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<relative>,
  start_line=<line>,
  end_line=<line+20>
)
```
**Extract:** all QueueAction enum values

## TASK 3
**Action:** Find QueueFilter class
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="QueueFilter"
)
```

## TASK 4
**Action:** Read QueueFilter body (same pattern as TASK 2)
**Extract:** all QueueFilter enum values

## TASK 5
**Action:** Search usage of each QueueAction value
For each action value:
```
fulltext_search(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  query="QueueAction.{VALUE}"
)
```
**Save:** `{value: [file_paths]}`

## TASK 6
**Action:** Search usage of each QueueFilter value (same pattern)

## TASK 7
**Action:** Map each QueueAction to queuemgr equivalent
```
| QueueAction value | queuemgr method              | notes        |
|-------------------|------------------------------|--------------|
| CANCEL            | integration.stop_job(job_id) |              |
| REMOVE            | integration.delete_job(job_id)|             |
| PAUSE             | (no equivalent — TODO)       | custom needed|
| RESUME            | integration.start_job(job_id)|              |
| RETRY             | (no equivalent — TODO)       | re-add job   |
```

## TASK 8
**Action:** Map each QueueFilter to queuemgr equivalent
```
| QueueFilter | queuemgr status filter | notes |
```

## TASK 9
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queue_action_filter_map.md",
  content=<both tables>
)
```

## DONE CHECK
- [ ] QueueAction values listed
- [ ] QueueFilter values listed
- [ ] Each value mapped or flagged TODO
- [ ] File written
