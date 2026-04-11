# Codex Elixir Phoenix: Framework Walkthrough

Welcome to the **Codex Elixir Phoenix** plugin! This framework is designed to provide a disciplined, autonomous, and safe development experience for Elixir, Phoenix, and LiveView applications.

The framework operates on a **Filesystem-based State Machine**. Your plans, tasks, and learnings are stored as markdown files, ensuring that your context is preserved across CLI sessions.

---

## 1. $phx-plan: The Architect's Foundation

The journey begins with `$phx-plan`. When you provide a natural language feature request, the **Planning Orchestrator** takes over.

- **Parallel Research**: It spawns 4 parallel sub-agents to scan your codebase (Schemas, Router, LiveViews, and Dependencies).
- **Execution Blueprint**: It generates a structured `plan.md` in `.codex/plans/{slug}/` containing a checklist of all required tasks.
- **Vibe-to-Code**: It translates your broad ideas into precise, sequential technical steps.

## 2. $phx-work: The Implementer's Engine

Once you have a plan, `$phx-work` is where the code is written.

- **Sequential execution**: The **Implementer Agent** tackles tasks one by one, focusing its context window on exactly what needs to be done.
- **Tight loops**: It follows a "Plan-Work-Verify" cycle within each task, refining its output until verification passes.
- **Resumable**: If you stop mid-sprint, just run `$phx-work` again to resume from the first unchecked box.

## 3. $phx-verify: The Quality Gate

Verification is not optional; it's a hard requirement. `$phx-verify` shells out to your host machine's native mix tooling.

- **Compilation**: Runs `mix compile --warnings-as-errors`.
- **Formatting**: Enforces `mix format`.
- **Consistency**: Runs `mix credo` and `mix test`.
- **Autonomous Recovery**: If compilation fails, the logs are fed directly back to the agent for self-correction.

## 4. $phx-review: The Peer Audit

Good code requires a second set of eyes. `$phx-review` spawns 4 specialist review agents in parallel:

- **Idiom Reviewer**: Ensures the code is "The Elixir Way."
- **Security Reviewer**: Checks for common vulnerabilities.
- **Performance Reviewer**: Looks for N+1 queries or socket bottlenecks.
- **Architectural Reviewer**: Validates alignment with existing project patterns.

## 5. $phx-compound: The Continuous Learner

The framework gets smarter as you use it. When a feature is complete, run `$phx-compound`.

- **Learning Extraction**: A specialist agent reviews the git diff and the original plan.
- **Persistent Memory**: It extracts architectural patterns or project-specific quirks into `.codex/agent-memory/`.
- **Avoid Repetition**: Future planning sessions will ingest this memory to avoid repeating past mistakes.

## 6. Iron Laws: The Unbreakable Guardrails

The **Iron Laws** are the framework's defining feature. They prevent catastrophic production bugs before they even reach your disk.

- **Deterministic Enforcement**: 22 `PreToolUse` hooks block dangerous patterns (e.g., `:float` for money, unsafe `String.to_atom`).
- **Semantic Enforcement**: The `iron-law-judge` agent monitors for deeper architectural violations (e.g., non-idempotent Oban jobs).
- **Hard Blockers**: If an Iron Law fires, the write is rejected until the agent reformulates the code to be safe.

---

### Ready to start?

Try running:
`$phx-plan create a simple "Hello World" LiveView page`
to see the planning phase in action!
