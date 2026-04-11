# JSON API Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/phoenix-contexts/references/json-api-patterns.md`

- Use controllers to translate HTTP into context calls and render JSON views or components for the response shape.
- Keep `action_fallback` in place so changesets and not-found errors are serialized consistently.
- Resolve auth and scope in the API pipeline before controller actions run.
- Validate request params at the context boundary with changesets rather than free-form map handling.
- Prefer stable response envelopes and status codes over ad hoc controller branches.
