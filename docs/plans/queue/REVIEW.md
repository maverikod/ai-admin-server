# Plan Review: Issues Found and Fixed

## ALL ISSUES RESOLVED

---

## Issues Fixed

### 1. CRITICAL: Wrong step order — delete before tests
**Status: ✔ FIXED**
- INDEX.md reordered: Step 5=Tests, Step 6=Delete legacy, Step 7=Final cleanup
- step_5/INDEX.md: now describes Tests (with Gate to Step 6)
- step_5/TASKS.md: replaced with test tasks (cst_create_file pattern)
- step_6/INDEX.md: now describes Delete legacy layer
- step_6/TASKS.md: replaced with deletion tasks
- step_7/INDEX.md: now describes Final cleanup
- step_7/TASKS.md: replaced with format/lint/typecheck/hard-delete tasks

### 2. CRITICAL: `create_text_file` used for .py files
**Status: ✔ FIXED in all affected files**
- step_2/2_1/TASKS.md: `__init__.py` now uses `cst_create_file`
- step_2/2_2/TASKS.md: `docker_job.py` now uses `cst_create_file`
- step_2/2_3_to_2_10/TASKS.md: CRITICAL header added, all jobs use `cst_create_file`
- step_3/TASKS.md: `__init__.py`, `integration.py`, `smoke_test_queue.py` all use `cst_create_file`
- step_5/TASKS.md: test files now use `cst_create_file`

### 3. MODERATE: Broken links in INDEX files
**Status: ✔ FIXED**
- step_2/INDEX.md: links updated to real TASKS.md paths
- step_3/INDEX.md: links updated to TASKS.md anchors (no more 3_2/...3_10/ references)
- step_4/INDEX.md: links updated to TASKS.md
- step_5/INDEX.md: rewritten for Tests step, links to TASKS.md anchors
- step_6/INDEX.md: rewritten for Delete step, links to TASKS.md anchors
- step_7/INDEX.md: rewritten for Cleanup step, links to TASKS.md anchors

### 4. MODERATE: Inconsistent command file paths in Step 4
**Status: ✔ FIXED**
- step_4/TASKS.md: TASK 0 added (discover real paths via list_project_files)
- Table now shows ??? placeholders with instruction to replace from TASK 0
- Step 1.1 instruction updated to find real paths

### 5. LOW: Step 5.8 references file deleted in Step 5.4
**Status: ✔ FIXED (automatically)**
- Eliminated by new step order: deletion is now Step 6, Step 5 is tests only

### 6. LOW: Step 6 "independent of migration" contradicts TASKS
**Status: ✔ FIXED**
- Old Step 6 duplicate diffs (6.1-6.5) moved to Step 1 (audit)
- New Step 6 is Delete legacy layer (clearly depends on Step 4+5 completion)
- step_6/INDEX.md has explicit Pre-condition: Step 5 gate must be cleared

### 7. LOW: Duplicate `### TASK 4` in step_3/TASKS.md
**Status: ✔ FIXED**
- step_3/TASKS.md rewritten completely (clean version)

---

## Files Modified (total)

| File | Change |
|------|--------|
| docs/plans/INDEX.md | Reordered steps, added .py creation note, added New Files section |
| docs/plans/step_1/INDEX.md | Added output artifacts, duplicate diff note, command paths note |
| docs/plans/step_2/INDEX.md | Added TASKS.md column to table, cst_create_file note |
| docs/plans/step_2/2_1/TASKS.md | cst_create_file for __init__.py, validate=False note |
| docs/plans/step_2/2_2/TASKS.md | cst_create_file for docker_job.py, format_code added |
| docs/plans/step_2/2_3_to_2_10/TASKS.md | CRITICAL header + cst_create_file pattern |
| docs/plans/step_3/INDEX.md | Fixed links to TASKS.md anchors |
| docs/plans/step_3/TASKS.md | Full rewrite: cst_create_file for all .py, no duplicates |
| docs/plans/step_4/INDEX.md | Fixed links, added TASK 0 note |
| docs/plans/step_4/TASKS.md | TASK 0 added, paths marked as PLACEHOLDER |
| docs/plans/step_5/INDEX.md | Rewritten: Tests step with Gate to Step 6 |
| docs/plans/step_5/TASKS.md | Rewritten: test tasks with cst_create_file |
| docs/plans/step_6/INDEX.md | Rewritten: Delete legacy layer |
| docs/plans/step_6/TASKS.md | Rewritten: deletion + deduplication tasks |
| docs/plans/step_7/INDEX.md | Rewritten: Final cleanup |
| docs/plans/step_7/TASKS.md | Rewritten: format/lint/typecheck/hard-delete |

## No Remaining Known Issues
