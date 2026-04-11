# Queries Reference

Source sample: `plugins/elixir-phoenix/skills/ecto-patterns/references/queries.md`

- Build composable query helpers instead of one-off `Repo.all/1` calls with inline filters.
- Use `dynamic/2` to assemble optional filters safely, and always pin external values with `^`.
- Preload collections in bulk to avoid N+1 queries; join only when the relationship shape justifies it.
- Keep JSONB filtering in the database with `json_extract_path/2` or equivalent SQL-safe expressions.
- Prefer `Repo.get/2` plus explicit not-found handling for user input instead of raising with `Repo.get!/2`.
