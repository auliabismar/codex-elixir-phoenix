# Story 4.1: Iron Law PreToolUse Hook Gateway Architecture

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an orchestrator,
I want the foundational Python hook gateway configured reliably,
so that any code generation attempt securely triggers regex constraints in under 500ms before Codex merges code to disk.

## Acceptance Criteria

1. **Given** an active `$phx-work` session approaching code execution
2. **When** Codex is about to write an `.ex` or `.exs` file
3. **Then** `hooks.json` intercepts the write and routes it through the independent Python hook gateway
4. **And** any blocked write emits the exact `IRON LAW VIOLATION: {Reasoning}. Require: {Prescribed Correction}.` message and exits non-zero

## Tasks / Subtasks

- [x] Register `PreToolUse` in `.codex/hooks.json` without breaking the existing `SessionStart` validation hook. (AC: 1, 2, 3)
  - [x] Add the new hook entry using the same script contract already in use for `SessionStart` (`type`, `path`, `runtime`).
  - [x] Preserve the current `SessionStart` mapping and JSON structure; do not replace or reformat the file unnecessarily.
  - [x] Keep the hook path inside the shipped `.codex/hooks/` payload so setup scripts continue to copy it unchanged.
- [x] Implement the lightweight Iron Law gateway entrypoint as a deterministic dispatcher. (AC: 1, 2, 3)
  - [x] Create `.codex/hooks/iron_law_gateway.py` as the single `PreToolUse` entrypoint for the first Epic 4 story.
  - [x] Parse the hook payload defensively and fail closed on malformed JSON, missing fields, or unknown event shapes.
  - [x] Route only `.ex` and `.exs` write attempts into the gateway logic; unrelated files and non-write events should pass through immediately.
  - [x] Keep the fast path stdlib-only and avoid filesystem scans or shell subprocesses on every invocation so the hook stays inside the latency budget.
- [x] Define the gateway contract for blocking, allowing, and extension points. (AC: 2, 3, 4)
  - [x] Emit the exact Iron Law message format on block: `IRON LAW VIOLATION: {Reasoning}. Require: {Prescribed Correction}.`
  - [x] Centralize the rule ordering in a small registry so later stories can add independent Python rule modules without rewriting the gateway.
  - [x] Treat missing rule modules or import failures as hard failures, not silent allow paths.
  - [x] Keep the gateway scope narrow: this story establishes the entrypoint and dispatch contract, not the individual Iron Law detectors.
- [x] Add pytest coverage for the gateway and hook wiring. (AC: 1, 2, 3, 4)
  - [x] Verify `.codex/hooks.json` still contains `SessionStart` and now also wires `PreToolUse` to the new gateway script.
  - [x] Verify `.ex` / `.exs` payloads reach the gateway and unrelated files are ignored on the fast path.
  - [x] Verify malformed payloads and missing rule modules fail closed with actionable error output.
  - [x] Add a focused low-overhead test for the no-op path so the gateway does not regress into expensive per-invocation discovery.

## Dev Notes

- **Story intent**
  - This is the first Epic 4 implementation story. Use it to establish the hook gateway and registration path only.
  - Do not implement the specific Iron Law detectors here; stories 4.2 through 4.4 own the actual rule logic for `:float`, `String.to_atom`, LiveView lifecycle, and Oban idempotency.
  - The important outcome is a stable, fail-closed `PreToolUse` entrypoint that can host later independent rule modules without becoming a monolithic router.

- **Architecture guardrails**
  - Follow the architecture decision to keep deterministic enforcement in independent Python scripts mapped through `hooks.json`.
  - Keep the gateway under the 500ms latency budget by avoiding directory scans, dynamic discovery, or shelling out on the hot path.
  - Use the exact block message format required by the architecture: `IRON LAW VIOLATION: {Reasoning}. Require: {Prescribed Correction}.`
  - Preserve the current `SessionStart` hook entry in `.codex/hooks.json`; this story adds `PreToolUse`, it does not replace session validation.
  - Keep the shipped runtime in `.codex/hooks/` and the tests in `tests/`; do not widen scope into agents or skills.
  - Use stdlib-first Python and cross-platform-safe file handling, matching the existing shipped hook style in this repo.

- **Implementation guidance**
  - Mirror the simple, importable helper style already used by `.codex/hooks/plan_work.py` and `.codex/hooks/reference_router.py`.
  - Fail closed for malformed hook payloads or unsupported event shapes; do not let parsing ambiguities silently become allowed writes.
  - Keep the gateway behavior explicit: allow unrelated writes quickly, block only when the rule registry says to block, and make the reason easy for the agent to act on.
  - Prefer a small, clearly named registry or manifest over hard-coded branching that will need to be rewritten in later stories.

- **Project structure notes**
  - Expected touch points are `.codex/hooks.json`, `.codex/hooks/iron_law_gateway.py`, and one focused pytest file under `tests/`.
  - `.codex/hooks.json` currently only wires `SessionStart`; update it in place and preserve comments/formatting style where possible.
  - No `project-context.md` was found, so rely on the planning artifacts and the existing shipped hook modules for conventions.
  - This story should leave room for later hook modules to be added without changing the gateway contract.

## References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Deterministic Guardrails (Iron Laws)]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1: Iron Law PreToolUse Hook Gateway Architecture]
- [Source: _bmad-output/planning-artifacts/prd.md#Iron Law Enforcement]
- [Source: _bmad-output/planning-artifacts/prd.md#Developer Tool / CLI Plugin Specific Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Plugin Execution & Hooks Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure & Format Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: .codex/hooks.json]
- [Source: .codex/hooks/validate_session.py]
- [Source: .codex/hooks/plan_work.py]
- [Source: .codex/hooks/reference_router.py]
- [Source: .codex/agents/iron-law-judge.toml]
- [Source: .codex/skills/phx-intro/WALKTHROUGH.md]

## Dev Agent Record

### Agent Model Used

Antigravity (Amelia)

### Debug Log References

N/A

### Completion Notes List

- Implemented `iron_law_gateway.py` with stdlib-only focus for latency budget.
- Registered `PreToolUse` hook in `.codex/hooks.json` alongside `SessionStart`.
- Established `rule_registry` pattern for independent rule modules.
- Added comprehensive pytest coverage for wiring, fast-path, and fail-closed logic.
- Verified all tests pass.
- 2026-04-12: Addressed code review findings for fail-closed payload handling, explicit non-write bypass, apply-patch target detection, and deterministic conflict-order coverage. Status moved to done.

### File List

- `.codex/hooks.json`
- `.codex/hooks/iron_law_gateway.py`
- `tests/test_iron_law_gateway.py`
