# Authorization Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/security/references/authorization.md`

- Policy checks belong in contexts and should be re-applied inside LiveView event handlers.
- Scope queries so users only see records they are entitled to access.
- Use explicit policy modules or behaviour-based policy checks instead of scattered inline conditionals.
- Mount-time authorization is not enough for LiveView; re-check mutating events.
- Fail closed on unauthorized access and return a predictable error path.
