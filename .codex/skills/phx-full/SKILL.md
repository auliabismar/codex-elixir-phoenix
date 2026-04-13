# Skill: Fully Autonomous Lifecycle (`$phx-full`)

Unified lifecycle automation orchestrating plan creation, implementation, verification, review, and compounding.

## Meta

- **ID:** `phx-full`
- **Commands:** `$phx-full`
- **Stage:** `orchestration`
- **Tier:** `logic`

## Usage

State a requirement to start a fresh autonomous cycle, or provide a target to resume/review.

```bash
# Start a new feature from scratch
$phx-full build email password authentication workflows

# Resume an existing plan by slug
$phx-full 20240413-auth-logic

# Resume an existing plan by path
$phx-full .codex/plans/20240413-auth-logic/plan.md

# Auto-resume (only if exactly one incomplete plan exists)
$phx-full
```

## Lifecycle Flow

1.  **Plan:** `phx-plan` (Discovery -> Roster -> Synthesis -> Plan)
2.  **Loop:**
    - **Work:** `phx-work` (Implementation)
    - **Verify:** `phx-verify` (Compile & Format Check)
    - **Retry:** Bounded recovery (up to 3 consecutive failures)
3.  **Review:** `phx-review` (Multi-domain Review -> Semantic Iron Law)
4.  **Rollback:** If semantic blocks found, reopen task and repeat Loop.
5.  **Rework:** If advisory findings found, fix and repeat Loop.
6.  **Compound:** `phx-compound` (Learning extraction & persistence)

## Orchestration Boundaries

- **Halt Condition:** More than 3 consecutive verification failures on the same task.
- **Fail-Closed:** Ambiguous targets or missing context stop the cycle.
- **Source of Truth:** `.codex/plans/{slug}/plan.md` tracks all progress.
