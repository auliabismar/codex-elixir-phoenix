# Migrations Reference

Source sample: `plugins/elixir-phoenix/skills/ecto-patterns/references/migrations.md`

- For destructive or large-table changes, split the rollout into add nullable column, backfill, then enforce `null: false`.
- Use concurrent indexes for PostgreSQL production tables when downtime matters.
- Keep data backfills explicit and reversible; do not hide application business logic inside migrations.
- Add constraints and foreign keys in the database so race conditions are blocked at the source.
- Review long-running migrations for lock duration before shipping them to production.
