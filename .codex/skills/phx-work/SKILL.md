---
name: phx-work
description: Use when the user invokes $phx-work. Resume the next pending task from an active markdown plan.
---

# Phoenix Work

This skill allows the framework to autonomously resume implementation from the first pending checkbox (`- [ ]`) in an active markdown plan.

## Instructions

1.  **Identify the Plan**:
    - Use `plan_work.resolve_active_plan(repo_root, target)` to resolve the active plan path.
    - `target` may be omitted, a slug (for example, `$phx-work feature-xyz`), or an explicit plan path inside `.codex/plans/`.
    - If no target is provided, the hook will auto-resume only when exactly one incomplete plan exists; otherwise it must fail closed and ask the user to choose.

2.  **Extract Task Context**:
    - Use `plan_work.get_work_context(plan_path)` to retrieve:
        - The current `task` text.
        - The overall `goal`.
        - Any implementation `notes`.
        - List of `completed_tasks` for context.
    - If `complete` is `true`, report that the plan is already complete and stop without modifying the file.

3.  **Execute Single Task**:
    - Scope your implementation **strictly** to the retrieved task.
    - Do NOT move on to the next task in the same invocation.

4.  **Mark Task Complete**:
    - Once the work is successfully implemented and verified, use `plan_work.complete_current_task(plan_path, task_index)` to persist the state.
    - This must mark only the targeted first pending task, and it must do nothing if the plan is already complete.
    - This ensures the markdown file remains the sole source of truth.

## Usage Examples

- `$phx-work`: Automatically resumes the single active plan in the repo.
- `$phx-work invoice-pdf`: Targets a specific plan slug if multiple are in progress.
- `$phx-work .codex/plans/invoice-pdf/plan.md`: Targets an explicit plan path inside the repo.
