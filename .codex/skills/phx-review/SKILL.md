---
name: phx-review
description: Use when the user invokes $phx-review. Performs multi-agent semantic review of implemented changes.
---

# Phoenix Review

This skill runs a manual semantic review cycle against the current implementation diff.

## Instructions

1. **Manual Trigger Only**:
   - Execute only when the user explicitly invokes `$phx-review`.
   - Do not auto-trigger from other lifecycle phases.

2. **Enforce Verification Prerequisite**:
   - Build the packet with `review_packet.collect_review_packet(repo_root)`.
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

6. **Story 5.2 Boundary**:
   - Synthesize findings only.
   - Do not mark semantic violations as final blockers and do not mutate lifecycle completion state here; enforcement and rollback belong to Story 5.3.

## Usage Examples

- `$phx-review`
- `$phx-review "Review current implementation diff"`
