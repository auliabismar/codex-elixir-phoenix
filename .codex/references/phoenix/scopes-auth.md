# Scopes and Authorization Reference

Source sample: `plugins/elixir-phoenix/skills/phoenix-contexts/references/scopes-auth.md`

- Phoenix 1.8+ projects should push a `%Scope{}`-style struct through contexts so data access is scoped by default.
- Build the scope in plugs or LiveView hooks, then augment it for tenant or organization routing when needed.
- Keep authentication, resource fetch, and authorization plugs separate so each step has one job.
- API pipelines should resolve the current scope from bearer tokens before controller code runs.
- Older Phoenix apps can use an authority struct as a migration bridge, but the calling pattern should still stay explicit.
