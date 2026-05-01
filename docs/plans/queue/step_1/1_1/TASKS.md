# 1.1 TASKS — Atomic Instructions for Haiku

Each task is ONE tool call. Execute in order. Do not skip.

---

## TASK 1
**Action:** Call find_usages  
**Command:**
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="QueueManager",
  target_type="class"
)
```
**Save result to variable:** `usages`  
**Expected:** list of dicts with keys: file_path, line, usage_type, context

---

## TASK 2
**Action:** Filter usages where usage_type == "import"  
**Input:** `usages` from TASK 1  
**Code:**
```python
import_files = [u["file_path"] for u in usages if u["usage_type"] == "import"]
```
**Save result to variable:** `import_files`

---

## TASK 3
**Action:** Filter usages where usage_type == "instantiation" or "call"  
**Input:** `usages` from TASK 1  
**Code:**
```python
call_sites = [(u["file_path"], u["line"], u.get("context","")) for u in usages if u["usage_type"] in ("instantiation","call")]
```
**Save result to variable:** `call_sites`

---

## TASK 4
**Action:** Deduplicate `import_files`, sort alphabetically  
**Code:**
```python
import_files = sorted(set(import_files))
```

---

## TASK 5
**Action:** For each file in `import_files`, find which `add_*_task` methods are called  
**For each file_path:**
```
find_usages(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  target_name="add_push_task",   # repeat for each add_* method
  target_type="method"
)
```
**Note:** Run for each method name: add_push_task, add_git_task, add_github_task,
add_build_task, add_pull_task, add_ollama_pull_task, add_ollama_run_task,
add_k8s_deployment_create_task, add_k8s_pod_create_task, add_k8s_cluster_create_task,
add_k8s_certificate_create_task, add_k8s_mtls_setup_task, add_vast_create_task,
add_vast_destroy_task, add_vast_search_task, add_vast_instances_task,
add_system_task, add_ssl_task, add_task, push_task  
**Build dict:** `{file_path: [list of add_*_task method names called]}`

---

## TASK 6
**Action:** Build markdown table string  
**Format:**
```
| file | methods_called |
|------|----------------|
| ai_admin/commands/vast_create_command.py | add_vast_create_task |
```
**Code:** iterate `import_files`, look up methods from TASK 5 dict

---

## TASK 7
**Action:** Write table to file  
**Command:**
```
create_text_file(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  file_path="docs/plans/step_1/queuemanager_importers.md",
  content=<table string from TASK 6>
)
```
**Expected:** file created, no error

---

## TASK 8
**Action:** Verify file was written  
**Command:**
```
list_project_files(
  project_id="c86dded6-6f93-4fb0-be54-b6d7b739eeb9",
  glob="docs/plans/step_1/queuemanager_importers.md"
)
```
**Expected:** count=1

---

## DONE CHECK
- [ ] `queuemanager_importers.md` exists
- [ ] Every importing file is listed
- [ ] Methods column is filled for each file
- [ ] No file has empty methods column without investigation
