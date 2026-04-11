# Plug Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/phoenix-contexts/references/plug-patterns.md`

- Use function plugs for small endpoint-specific logic and module plugs for reusable pipelines.
- Fetch identity or scope before authorization plugs so policy code receives complete context.
- Halt the connection immediately on rejected access instead of letting the pipeline continue.
- Keep plugs focused on HTTP concerns such as session, params, and request gating; move business logic back into contexts.
- Name plugs after the state they establish, such as `fetch_current_scope` or `require_authenticated_user`.
