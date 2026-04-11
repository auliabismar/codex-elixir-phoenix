# Changesets Reference

Source sample: `plugins/elixir-phoenix/skills/ecto-patterns/references/changesets.md`

- Use `cast/4` for external input and `put_change/3` or `change/2` for trusted internal data.
- Split schema mutations into operation-specific changesets such as registration, profile, password, and admin edits.
- Keep transaction-aware mutations inside `prepare_changes/2` instead of controller or LiveView code.
- Use `embedded_schema` only when the child record is owned by the parent and never queried independently.
- Prefer `:integer` or `:decimal` for money; never store money as `:float`.
