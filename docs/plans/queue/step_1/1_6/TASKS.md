# 1.6 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Get FTPExecutor methods
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="FTPExecutor"
)
```
**Save:** `ftp_upper_methods`

## TASK 2
**Action:** Get FtpExecutor methods
```
list_class_methods(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  class_name="FtpExecutor"
)
```
**Save:** `ftp_lower_methods`

## TASK 3
**Action:** Find FTPExecutor file_path
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="FTPExecutor"
)
```
**Save:** `ftpupper_path` = entities[0]["file_path"]

## TASK 4
**Action:** Find FtpExecutor file_path
```
get_code_entity_info(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  entity_type="class",
  entity_name="FtpExecutor"
)
```
**Save:** `ftplower_path` = entities[0]["file_path"]

## TASK 5
**Action:** Read FTPExecutor file (full)
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<ftpupper_path relative>
)
```
**Note:** extract: connection logic, auth logic, transfer logic

## TASK 6
**Action:** Read FtpExecutor file (full)
```
universal_file_read(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path=<ftplower_path relative>
)
```
**Note:** extract: connection logic, auth logic, transfer logic

## TASK 7
**Action:** Compute method sets
```python
names_upper = set(m["name"] for m in ftp_upper_methods)
names_lower = set(m["name"] for m in ftp_lower_methods)
only_upper = names_upper - names_lower
only_lower = names_lower - names_upper
shared = names_upper & names_lower
```

## TASK 8
**Action:** For each method in `only_upper`: check if it has real logic or is stub (has_pass=True)
For each method in `only_lower`: same check

## TASK 9
**Action:** Build report:
```
## FTP Executor Diff
- FTPExecutor ({N} methods): {file}
- FtpExecutor ({M} methods): {file}
- Only in FTPExecutor: [...] — real/stub
- Only in FtpExecutor: [...] — real/stub
- Shared: [...]
- Merge strategy: keep all real logic from both in FtpJob.run()
- Methods to port to FtpJob: [complete list]
```

## TASK 10
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/ftp_executor_diff.md",
  content=<report>
)
```

## DONE CHECK
- [ ] Both executors read
- [ ] Method diff computed
- [ ] Stubs flagged
- [ ] Full merge method list produced
- [ ] File written
