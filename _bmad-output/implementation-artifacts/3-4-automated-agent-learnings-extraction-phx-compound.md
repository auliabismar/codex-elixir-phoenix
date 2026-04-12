# Story 3.4: Automated Agent Learnings Extraction (`$phx-compound`)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a long-term user,
I want the system to extract architectural learnings from resolved feature implementations natively,
so that future sprints don't systematically repeat the exact same errors inside my specific repository boundaries.

## Acceptance Criteria

1. **Given** a fully completed and verified implementation plan
2. **When** the user manually executes the `$phx-compound` command
3. **Then** a designated analytics agent reviews the git diff implementation against the original plan intent
4. **And** correctly persists deduced application boundaries or generalized implementation quirks reliably into `.codex/agent-memory/`

## Tasks / Subtasks

- [x] Add the manual `$phx-compound` skill entrypoint and command contract. (AC: 1, 2)
  - [x] Create `.codex/skills/phx-compound/SKILL.md` using the same frontmatter and terse instruction style as `phx-plan`, `phx-work`, `phx-review`, and `phx-verify`.
  - [x] Define `target` resolution rules up front: allow omitted target, plan slug, or explicit `.codex/plans/.../plan.md` path; auto-resolve only when exactly one eligible plan exists and otherwise fail closed with a clear selection message.
  - [x] Keep the command manual-only for this story; do not auto-trigger compounding from `PostToolUse` hooks or `hooks.json`.
  - [x] Reuse the existing `workflow-orchestrator` as the designated analytics agent for v1 instead of introducing a 21st TOML agent.
- [x] Implement a deterministic helper for plan and diff collection. (AC: 1, 3)
  - [x] Add a standalone Python module in `.codex/hooks/` with `snake_case` naming that resolves the target plan safely inside `.codex/plans/`.
  - [x] Reuse existing plan parsing helpers where possible (`plan_work.py`, `plan_state.py`) rather than re-implementing markdown state parsing from scratch.
  - [x] Gather the current feature diff in the same spirit as `$phx-review`: operate on the current repository diff and fail closed with an actionable message when there is no meaningful diff to analyze.
- [x] Persist reusable learnings into `.codex/agent-memory/` with a stable markdown schema. (AC: 3, 4)
  - [x] Write memory files as markdown that future agents can ingest directly, including source plan, source diff basis, reusable boundaries, repository-specific quirks, and avoid/repeat guidance.
  - [x] Use one durable memory file per plan slug, for example `.codex/agent-memory/{slug}.md`, with append-only dated sections rather than ephemeral temp files or opaque JSON blobs.
  - [x] Preserve existing user-created memory files; do not delete or overwrite unrelated notes during compounding.
  - [x] If a memory file already exists for the same plan slug, append or merge safely instead of clobbering prior learnings.
- [x] Add verification coverage for the deterministic parts of the workflow. (AC: 1, 2, 3, 4)
  - [x] Add pytest coverage for safe plan resolution, empty-diff handling, markdown memory file generation, and non-destructive persistence behavior.
  - [x] Follow the existing `tests/test_plan_work.py` and `tests/test_reference_router.py` pattern: import shipped modules directly from `.codex/hooks/` and test repository-like temp directories.
  - [x] Keep LLM reasoning thin and test the helper boundaries, file contracts, and failure modes instead of attempting to unit test the model output itself.

### Review Findings

- [x] [Review][Patch] Restrict explicit targets to `.codex/plans/.../plan.md` paths only [.codex/hooks/plan_compound.py:154]
- [x] [Review][Patch] Fail closed on diff collection errors and include untracked feature files [.codex/hooks/plan_compound.py:219]
- [x] [Review][Patch] Reject malformed plans with no recognized tasks during auto-resolution [.codex/hooks/plan_compound.py:201]
- [x] [Review][Patch] Persist learnings with the story's stable markdown schema instead of opaque freeform content [.codex/hooks/plan_compound.py:124]

## Dev Notes

- **Story intent**
  - This is the last story in Epic 3 and closes the loop after planning, work routing, and review. The command should turn completed implementation context into durable repository memory, not into another hidden state system.
  - The shortest path is a manual `$phx-compound` skill backed by deterministic diff/plan collection plus a structured markdown write into `.codex/agent-memory/`.
- **Architecture guardrails**
  - Keep Codex-facing assets in `kebab-case` and Python helpers in `snake_case`.
  - Keep filesystem state explicit. Plans stay in `.codex/plans/{slug}/plan.md`; compounded learnings live in `.codex/agent-memory/`; avoid any in-memory-only persistence mechanism.
  - Stay within the current architecture's 20-agent model tier map. `workflow-orchestrator.toml` already claims responsibility for `$phx-compound`, so reuse or tighten that path before inventing new agents.
  - Treat this story as manual lifecycle plumbing, not Wave-6 `PostToolUse` analytics. The PRD and architecture mention future analytics hooks, but this story's acceptance criteria are satisfied by an explicit user-invoked command.
- **Concrete implementation direction**
  - Mirror the existing skill pattern used by `.codex/skills/phx-work/SKILL.md` and the other `phx-*` commands: concise frontmatter, short instructions, explicit scope.
  - Mirror the target-selection contract used by `$phx-work`: explicit target beats slug, slug beats auto-discovery, and ambiguous auto-discovery must stop with a user-facing error instead of guessing.
  - Mirror the existing hook/test pattern used by `.codex/hooks/plan_work.py` and `.codex/hooks/reference_router.py`: standalone importable helpers, path-safe resolution, UTF-8 reads/writes, and deterministic fallback behavior.
  - Prefer passing a structured packet to the analytics prompt: plan goal, remaining/completed tasks, relevant notes, and the current git diff text. Do not ask the model to rediscover repository state blindly.
  - Write memory artifacts as markdown that are easy to inspect and diff. Standardize on a per-plan slug file with dated sections so future agents have one predictable lookup location per completed feature.
- **Previous story intelligence**
  - Story 3.3 established contextual reference injection and current `.codex` testing conventions. Reuse its patterns for path resolution and deterministic helper design.
  - Story 3.3 also left review follow-ups around routing quality and reference-doc completeness. Do not couple `$phx-compound` to those unresolved items; this story should work even if reference routing remains imperfect.
- **Git intelligence**
  - Recent commits show the repo is currently extending `.codex/hooks/`, `.codex/skills/`, `.codex/agents/`, and `tests/` in lockstep. Keep that same shape for this story.
  - `e3cf39e` integrated reference routing via a new hook module plus targeted pytest files. `0d82128` expanded markdown reference docs. Follow the hook-plus-tests delivery pattern rather than introducing a separate framework.
- **Testing expectations**
  - Use pytest for deterministic helper coverage.
  - Favor temp-repo fixtures that create `.codex/plans/`, `.codex/agent-memory/`, and a lightweight git repository shape as needed.
  - Validate failure messages for no plan, ambiguous plan, and empty diff scenarios so the manual command fails clearly.
- **Out of scope**
  - Automatic `PostToolUse` analytics wiring.
  - Reworking the 20-agent inventory into a larger roster.
  - Cleaning up Story 3.3 review findings unless they directly block compounding.

### Project Structure Notes

- Expected touch points for implementation are `.codex/skills/phx-compound/`, `.codex/hooks/`, `.codex/agent-memory/`, `tests/`, and only the minimum supporting updates in existing `.codex/agents/` or intro docs if the command contract must be clarified.
- `.codex/hooks.json` currently only wires `SessionStart`; it should remain unchanged for this manual story unless a truly minimal clarification is required elsewhere.
- No dedicated UX artifact or `project-context.md` was found for this story. Keep user-facing copy aligned with the existing `phx-*` skill docs and the intro walkthrough.
- Preserve the development/distribution boundary from the architecture: test harnesses remain in `tests/`, while shipped runtime behavior stays under `.codex/`.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3: Agentic Intelligence & Orchestration]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4: Automated Agent Learnings Extraction (`$phx-compound`)]
- [Source: _bmad-output/planning-artifacts/prd.md#Lifecycle Orchestration]
- [Source: _bmad-output/planning-artifacts/prd.md#Functional Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Plugin Execution & Hooks Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Model Tier Routing Strategy]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/implementation-artifacts/3-3-contextual-reference-document-routing.md]
- [Source: .codex/agents/workflow-orchestrator.toml]
- [Source: .codex/skills/phx-intro/WALKTHROUGH.md#5. $phx-compound: The Continuous Learner]
- [Source: tests/test_plan_work.py]
- [Source: tests/test_reference_router.py]

## Dev Agent Record

### Agent Model Used

Codex GPT-5 (Bob via `bmad-create-story`)

### Debug Log References

- N/A

### Completion Notes List

- 2026-04-12: Implementation complete. Skill created, hook implemented with git diff analysis and learning persistence. Pytest coverage added and verified. Status updated to review.

### File List

- `.codex/skills/phx-compound/SKILL.md`: Skill definition and manual entrypoint
- `.codex/hooks/plan_compound.py`: Deterministic analysis packet and memory persistence
- `tests/test_plan_compound.py`: Test suite for compounding logic
- `.codex/agent-memory/`: Directory for persistent learnings (empty initially)
