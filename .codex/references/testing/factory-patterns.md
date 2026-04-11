# Factory Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/testing/references/factory-patterns.md`

- Use `build/2` by default and only `insert/2` when the database is part of the behavior under test.
- Keep factories aligned with every field required by the schema changeset so they fail less noisily.
- Use sequences for unique emails, slugs, and identifiers instead of hard-coded values.
- Model common variants with traits or helper constructors instead of duplicating factory bodies.
- Keep cross-context fixtures thin and prefer context APIs when the setup itself is part of the feature.
