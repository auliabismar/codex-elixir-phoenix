---
name: phx-plan
description: Use when the user invokes $phx-plan. Create a systematic architectural and implementation plan persisted as markdown.
---

# Phoenix Plan

This skill translates natural language feature requests into a sequentially actionable, checkbox-based markdown sprint stored in `.codex/plans/{slug}/plan.md`.

## Instructions

1.  **Analyze Intent**: Elicit or summarize the feature request. Identify the core goal and any constraints.
2.  **Resolve Slug**: Normalize the feature request into a concise `kebab-case` slug. You MUST use the `normalize_slug` logic from `.codex/hooks/plan_builder.py` or equivalent filtering:
    - Strip leading imperative verbs (create, add, implement, etc.) and articles (a, an, the, and, of, etc.).
    - Example: "Create an invoice PDF generator" -> `invoice-pdf-generator`.
3.  **Check for Collisions**: Verify if `.codex/plans/{slug}/plan.md` already exists. If it does, inform the user and REFUSE to overwrite it unless they explicitly ask to replace it.
4.  **Generate Structured Plan**:
    - **Goal**: One or two sentences describing the outcome.
    - **Tasks**: An ordered list of specific, sequential tasks using exact canonical `[ ] ` syntax.
    - **Notes**: Implementation risks, validation targets, or context.
5.  **Persist Plan**: Use the `create_plan_file` logic from `.codex/hooks/plan_builder.py` to write the plan using the `.codex/plans/_template/plan.md` scaffold.
    - Ensure every task is in the `## Tasks` section.
    - Ensure exact checkbox syntax: `- [ ] ` (space after bracket).

## Usage Examples

- `$phx-plan "Add user authentication to the admin area"`
- `$phx-plan "generate an invoice PDF summary"`
