# 1.2 TASKS — Atomic Instructions for Haiku

## TASK 1
**Action:** Call find_usages for QueueClient
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="QueueClient",
  target_type="class"
)
```
**Save:** `usages`

## TASK 2
**Action:** Filter by usage_type == "import"
```python
import_files = sorted(set(u["file_path"] for u in usages if u["usage_type"] == "import"))
```
**Save:** `import_files`

## TASK 3
**Action:** Filter by usage_type == "instantiation"
```python
inst_sites = [(u["file_path"], u["line"], u.get("context","")) for u in usages if u["usage_type"] == "instantiation"]
```
**Save:** `inst_sites`

## TASK 4
**Action:** Build markdown table
```
| file | import | instantiation_line | context |
```
For each file in `import_files` combine with `inst_sites`.

## TASK 5
**Action:** Append note to table:
> QueueClient is a facade over QueueManager singleton. All usages will be deleted in Step 5.

## TASK 6
**Action:** Write file
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queueclient_importers.md",
  content=<table>
)
```

## TASK 7
**Action:** Verify
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="docs/plans/step_1/queueclient_importers.md"
)
```
**Expected:** count=1

## DONE CHECK
- [ ] File written
- [ ] All QueueClient importers listed
- [ ] Note about deletion added
