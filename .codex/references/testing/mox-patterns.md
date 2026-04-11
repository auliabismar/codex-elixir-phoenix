# Mox Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/testing/references/mox-patterns.md`

- Mock only behaviour-backed external boundaries, not Ecto, standard library modules, or internal code paths.
- Call `verify_on_exit!/0` in tests that set expectations.
- Use `expect/4` for verified interactions and `stub/3` for default fallback behavior.
- When spawned processes need the same mock, grant access with `Mox.allow/3`.
- Global Mox mode requires `async: false` because expectations are shared.
