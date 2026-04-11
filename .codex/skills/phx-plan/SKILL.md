---
name: phx-plan
description: Use when the user invokes $phx-plan. Create a systematic architectural and implementation plan persisted as markdown.
---

# Phoenix Plan

This skill translates natural language feature requests into a sequentially actionable, checkbox-based markdown sprint stored in `.codex/plans/{slug}/plan.md`.

## Parallel Research Execution

When executing `$phx-plan`, you MUST spawn 4 parallel discovery sub-agents before finalizing any plan:

1. **ecto-schema-analyzer**: Analyzes `lib/*/schema/*.ex` and `lib/*/*.ex` for `Ecto.Schema` definitions
2. **phoenix-router-mapper**: Parses `lib/*_web/router.ex` to map endpoints and routes
3. **liveview-component-scanner**: Parses `lib/*_web/live/*` for LiveView lifecycle hooks and components
4. **dependency-auditor**: Parses `mix.exs` and `mix.lock` for version constraints and plugin support

### Concurrency Rules

- All 4 sub-agents run in parallel using the `parallel_spawn` configuration from `planning-orchestrator.toml`
- Each sub-agent returns structured XML output: `<discovery role="...">...</discovery>`
- Sub-agents MUST NOT write to `plan.md` directly - they return findings to the orchestrator
- If platform limits prevent true concurrency, fall back to sequential execution with timing logged

### Results Aggregation

- Use `plan_aggregator.py` to merge the 4 XML discovery blocks into a single prompt
- Implement conflict resolution for overlapping information (e.g., route-component mappings)
- Target execution time: < 60 seconds for standard Phoenix apps

## Instructions

1.  **Analyze Intent**: Elicit or summarize the feature request. Identify the core goal and any constraints.
2.  **Resolve Slug**: Normalize the feature request into a concise `kebab-case` slug. You MUST use the `normalize_slug` logic from `.codex/hooks/plan_builder.py` or equivalent filtering:
    - Strip leading imperative verbs (create, add, implement, etc.) and articles (a, an, the, and, of, etc.).
    - Example: "Create an invoice PDF generator" -> `invoice-pdf-generator`.
3.  **Check for Collisions**: Verify if `.codex/plans/{slug}/plan.md` already exists. If it does, inform the user and REFUSE to overwrite it unless they explicitly ask to replace it.
4.  **Spawn Parallel Research**: Run all 4 discovery sub-agents concurrently:
    - Use the role definitions from `planning-orchestrator.toml`
    - Collect XML-formatted results from each
5.  **Aggregate Results**: Merge outputs using `plan_aggregator.py`, resolving conflicts
6.  **Generate Structured Plan**:
    - **Goal**: One or two sentences describing the outcome.
    - **Tasks**: An ordered list of specific, sequential tasks using exact canonical `[ ] ` syntax.
    - **Notes**: Implementation risks, validation targets, or context.
7.  **Persist Plan**: Use the `create_plan_file` logic from `.codex/hooks/plan_builder.py` to write the plan using the `.codex/plans/_template/plan.md` scaffold.
    - Ensure every task is in the `## Tasks` section.
    - Ensure exact checkbox syntax: `- [ ] ` (space after bracket).

## Usage Examples

- `$phx-plan "Add user authentication to the admin area"`
- `$phx-plan "generate an invoice PDF summary"`
