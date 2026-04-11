# Routing Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/phoenix-contexts/references/routing-patterns.md`

- Prefer verified routes with the `~p` sigil and stop adding new `Routes.*_path` helper usage.
- Keep browser and API pipelines explicit and small, with auth and scope plugs applied deliberately.
- Do not introduce Rails-style service objects, decorators, concerns, or repository wrappers in Phoenix code.
- Delegate controller and LiveView data access to contexts instead of issuing ad hoc `Repo` queries in the web layer.
- Split oversized contexts when the domain language or ownership boundary has clearly diverged.
