# 1.10: Produce Final Dependency Matrix

## Atomic Steps
1. Aggregate results from 1.1–1.9 into one master table
2. Columns: Command class | add_*_task method | Executor class | Executor method | Job class (Step 2 target)
3. Add column: migration status (TODO / IN PROGRESS / DONE)
4. Add column: test coverage exists (YES / NO)
5. Cross-check: every row in 1.1 must appear in this matrix
6. Save as `docs/plans/step_1/dependency_matrix.md` — this is the migration checklist

## Example Row
```
VastCreateCommand | add_vast_create_task | VastExecutor | create() | VastJob | TODO | NO
```
