# Transactions Reference

Source sample: `plugins/elixir-phoenix/skills/ecto-patterns/references/transactions.md`

- Use `Repo.transact/1` for short linear flows and `Ecto.Multi` when the operation needs named steps or reusable composition.
- Put side effects such as mailers or broadcasts behind explicit `Multi.run/3` steps.
- Match on the failed Multi step name so callers know which branch rolled back.
- Use upserts deliberately with `on_conflict` and a concrete `conflict_target`.
- Reach for `Repo.stream/1` when processing large result sets that should not be loaded fully into memory.
