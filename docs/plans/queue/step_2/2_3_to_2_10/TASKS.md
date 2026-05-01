# 2.3–2.10 TASKS — Atomic Instructions for Haiku
# Template: same as 2.2, change executor/job/params per domain

## CRITICAL: Python file creation
**Use `cst_create_file` (NOT `create_text_file`) for all `.py` files.**
`create_text_file` only supports `.md/.txt/.rst/.adoc` and will FAIL on `.py`.

## Python file creation pattern (all Job files):
```
1. cst_create_file(project_id, file_path, docstring)  → returns tree_id
2. cst_modify_tree(tree_id, operations=[{insert class code}])  → add class to tree
3. cst_save_tree(tree_id, project_id, file_path, backup, validate)  → write to disk
4. cst_load_file(project_id, file_path)  → reload, get new tree_id
5. cst_find_node + cst_modify_tree  → replace NotImplementedError stubs with real logic
6. cst_save_tree  → persist final version
7. format_code + lint_code + type_check_code  → validate
```

# 2.3: GitJob

## TASK 1: Find GitExecutor
```
get_code_entity_info(project_id=PROJ, entity_type="class", entity_name="GitExecutor")
```

## TASK 2: Read GitExecutor full body
```
universal_file_read(project_id=PROJ, file_path=<path>)
```
Extract: clone(), push(), pull() methods + ssl_config handling

## TASK 3: Create ai_admin/jobs/git_job.py stub
Class: GitJob(QueueJobBase)
ops: clone | push | pull
params: operation_type, current_directory, repository_url, target_directory,
        branch, remote, force, ssl_config, user_roles

## TASK 4–6: CST load → find _clone/_push/_pull nodes → replace with real logic

## TASK 7: cst_save_tree (backup=True, validate=True)

## TASK 8: lint_code → expect error_count=0

## TASK 9: type_check_code → document issues

---

# 2.4: GitHubJob

## TASK 1: Find GitHubExecutor
```
get_code_entity_info(project_id=PROJ, entity_type="class", entity_name="GitHubExecutor")
```

## TASK 2: Read GitHubExecutor full body
Extract: all GitHub API operations + token auth logic

## TASK 3: Create ai_admin/jobs/github_job.py stub
Class: GitHubJob(QueueJobBase)
ops: as found in executor (create_repo, delete_repo, list_repos, etc.)
params: operation_type, repo_name, description, private, initialize,
        gitignore_template, license_template, username, token, ssl_config, user_roles

## TASK 4–6: CST load → find each op method → replace with real logic

## TASK 7: cst_save_tree
## TASK 8: lint_code
## TASK 9: type_check_code

---

# 2.5: K8sJob

## TASK 1: Find K8sExecutor
```
get_code_entity_info(project_id=PROJ, entity_type="class", entity_name="K8sExecutor")
```

## TASK 2: Find K8sKindExecutor
```
get_code_entity_info(project_id=PROJ, entity_type="class", entity_name="K8sKindExecutor")
```

## TASK 3: Find KindExecutor
```
get_code_entity_info(project_id=PROJ, entity_type="class", entity_name="KindExecutor")
```

## TASK 4: Read all three executor bodies
Three separate universal_file_read calls
Extract: deployment_create, pod_create, cluster_create, cert_create, mtls_setup

## TASK 5: Create ai_admin/jobs/k8s_job.py stub
Class: K8sJob(QueueJobBase)
ops: deploy | pod | cluster | cert | mtls
params: operation, project_path, image, port, namespace, replicas,
        cluster_name, cluster_type, cert_type, common_name

## TASK 6–8: CST load → replace each op method → save

## TASK 9: lint_code
## TASK 10: type_check_code

---

# 2.6: VastJob

## TASK 1: Find VastExecutor, read body
## TASK 2: Create ai_admin/jobs/vast_job.py stub
ops: create | destroy | search | list
params: operation, bundle_id, image, disk, label, onstart, env_vars,
        gpu_name, min_gpu_count, max_gpu_count, min_gpu_ram,
        max_price_per_hour, disk_space, order, limit,
        instance_id, show_all, user_roles

## TASK 3–5: CST load → replace ops → save
## TASK 6: lint + typecheck

---

# 2.7: FtpJob (merge FTPExecutor + FtpExecutor)

## TASK 1: Read ftp_executor_diff.md to get full method list
```
universal_file_read(project_id=PROJ, file_path="docs/plans/step_1/ftp_executor_diff.md")
```

## TASK 2: Read FTPExecutor body
## TASK 3: Read FtpExecutor body
## TASK 4: Create ai_admin/jobs/ftp_job.py stub
Class: FtpJob(QueueJobBase)
ops: upload | download | list | delete | mkdir
params: operation, host, port, username, password, local_path,
        remote_path, ssl_config, user_roles

## TASK 5–7: CST load → replace each op → save
## TASK 8: lint + typecheck

---

# 2.8: OllamaJob

## TASK 1: Find OllamaExecutor, read body
## TASK 2: Create ai_admin/jobs/ollama_job.py stub
ops: pull | run
params: operation, model_name, prompt, max_tokens, temperature

## TASK 3–5: CST load → replace pull/run → save
## TASK 6: lint + typecheck

---

# 2.9: SslJob

## TASK 1: Find SSLExecutor, read body
## TASK 2: Create ai_admin/jobs/ssl_job.py stub
ops: generate | view | verify | revoke
params: operation_type, cert_type, common_name, ssl_config, user_roles

## TASK 3–5: CST load → replace each op → save
## TASK 6: lint + typecheck

---

# 2.10: SystemJob

## TASK 1: Find SystemExecutor, read body
## TASK 2: Create ai_admin/jobs/system_job.py stub
ops: system_monitor
params: operation_type, include_gpu, include_temperature, include_processes,
        ssl_config, user_roles

## TASK 3–5: CST load → replace system_monitor → save

## TASK 6: Update ai_admin/jobs/__init__.py — ensure all 9 Job classes exported
```
cst_load_file(project_id=PROJ, file_path="ai_admin/jobs/__init__.py")
```
Verify all 9 imports present. If any missing, add via cst_modify_tree + cst_save_tree.

## TASK 7: lint_code on __init__.py
## TASK 8: type_check_code on __init__.py

## FINAL CHECK for all 2.x steps
- [ ] ai_admin/jobs/ has 10 files (__init__ + 9 jobs)
- [ ] Zero NotImplementedError remaining in any Job class
- [ ] lint_code passes on all files
- [ ] type_check_code passes or issues documented per file