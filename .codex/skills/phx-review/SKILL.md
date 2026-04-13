---
name: phx-review
description: Use when the user invokes $phx-review. Performs multi-agent semantic review of implemented changes.
---

# Phoenix Review

This skill runs a manual review cycle against the current implementation diff, then applies semantic Iron Law enforcement.

## Instructions

1. **Manual Trigger Only**:
   - Execute only when the user explicitly invokes `$phx-review`.
   - Do not auto-trigger from other lifecycle phases.

2. **Enforce Verification Prerequisite**:
   - Build the packet with `review_packet.collect_review_packet(repo_root, target=...)`.
   - If `ready` is `false`, stop immediately and return the structured packet (`error_type`, `message`, `verification`) without spawning reviewers.
   - Use only the existing `validate_compilation.validate_project(...)` gate behavior; do not broaden this skill into additional credo/test enforcement.

3. **Review Scope**:
   - Review only the packet's `git_diff` for the current working changes.
   - Do not review the full repository or unrelated historical commits.

4. **Parallel Reviewer Fan-out**:
   - Use the 4-domain roster configured in `.codex/agents/parallel-reviewer.toml`:
     - `idiom` via `elixir-reviewer`
     - `security` via `security-analyzer`
     - `performance` via `performance-reviewer`
     - `architecture` via `architecture-reviewer`
   - Pass the same packet to every reviewer: `repo_root`, `git_diff`, `source_diff_basis`, and `verification` metadata.

5. **Deterministic Aggregation**:
   - Require machine-readable reviewer output as direct `<finding>` entries or
     `<status>clean</status>`; the parallel coordinator wraps each reviewer in the
     outer `<review role="...">` block.
   - Aggregate via `review_aggregator.aggregate_review_outputs(outputs)`.
   - Return a stable prioritized checklist (High → Medium → Low), preserving reviewer identity and severity.

6. **Semantic Iron Law Gate (Story 5.3)**:
   - Run `iron-law-judge` as a separate pass after 4-reviewer synthesis.
   - Judge must return the strict XML contract:
     - clean: `<iron-law-review><status>clean</status></iron-law-review>`
     - violation: `<iron-law-review><status>violation</status><violation law="N"><title>...</title><reasoning>...</reasoning><correction>...</correction></violation></iron-law-review>`
   - Normalize verdicts through `review_enforcement.normalize_judge_output(...)`.
   - Keep semantic results distinct from advisory checklist findings.

7. **Plan Binding and Fail-Closed Rollback**:
   - Include plan context in the review packet via `plan_binding` (`plan_path`, `plan_slug`, status).
   - Support explicit review target (slug or plan path) when provided.
   - With no explicit target, resolve exactly one eligible plan; fail closed on no target or ambiguity.
   - Apply rollback only via `review_enforcement.enforce_semantic_gate(...)`, reusing the same `plan_binding` captured in the review packet instead of re-resolving target state.
   - If semantic violation occurs:
     - Reopen exactly one task (`most recently completed` = highest line-index `- [x]` in `## Tasks`).
     - Return structured violation payload and rollback metadata.
   - If target binding fails or no completed task exists, return structured fail-closed status and do **not** mutate `.codex/plans/`.

8. **Final Response Contract**:
   - Preserve the 4-domain checklist exactly for advisory findings.
   - Surface semantic verdict as a dedicated blocker section *before* the checklist via `review_enforcement.prepend_semantic_blocker(...)` when a violation exists.
   - Avoid duplicating deterministic `PreToolUse` hook violations already blocked earlier in the lifecycle.

## Usage Examples

- `$phx-review`
- `$phx-review payments`
- `$phx-review .codex/plans/payments/plan.md`
