---
name: phx-compound
description: Use when the user invokes $phx-compound. Extract architectural learnings from resolved feature implementations and persist them into agent memory.
---

# Phoenix Compound

This skill enables the framework to analyze a completed feature implementation (via git diff and original implementation plan) and deduce reusable architectural patterns, application boundaries, or repository-specific quirks for future reference.

## Instructions

1.  **Resolve the Target Plan**:
    - Use `plan_compound.resolve_target_plan(repo_root, target)` to identify the plan to analyze.
    - `target` may be omitted, a slug (for example, `$phx-compound feature-xyz`), or an explicit plan path inside `.codex/plans/`.
    - If no target is provided, auto-resolve only when exactly one eligible plan exists; otherwise, fail with a request for user selection.

2.  **Gather Context and Diff**:
    - Use `plan_compound.get_analysis_packet(plan_path)` to retrieve the implementation result:
        - The `plan_content`, `goal`, `notes`, and `completed_tasks` describing the original plan intent.
        - The current `git_diff` and `source_diff_basis` representing the feature implementation.
        - The completion `status` of the plan.
    - If the plan is incomplete or the diff cannot be collected cleanly, stop and inform the user instead of guessing.

3.  **Analyze and Extract Learnings**:
    - Pass the analysis packet to the designated analytics agent (`workflow-orchestrator`).
    - The agent must identify:
        - **Repository Boundaries**: Inferred structural or architectural rules.
        - **Implementation Quirks**: Specific way things are done in this repo (e.g., specific library patterns).
        - **Avoid/Repeat Guidance**: Deterministic advice for future similar tasks.

4.  **Persist Memory**:
    - Use `plan_compound.persist_learning(repo_root, slug, learning_payload)` to save the deduced patterns.
    - Learnings are stored in `.codex/agent-memory/{slug}.md`.
    - The persisted markdown must keep a stable section schema for source plan, source diff basis, repository boundaries, repository-specific quirks, avoid guidance, repeat guidance, and notes.
    - Content must be appended to dated sections if the file already exists; do not overwrite or delete existing notes.

## Usage Examples

- `$phx-compound`: Analyzes the single eligible plan if only one exists.
- `$phx-compound user-auth`: Analyzes the plan associated with the `user-auth` slug.
- `$phx-compound .codex/plans/user-auth/plan.md`: Targets an explicit plan file.
