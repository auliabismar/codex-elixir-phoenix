# Ecto Repo Patterns

## Key Points
- Keep raw `Repo` calls inside contexts or persistence modules.
- Use `Repo.one/2`, `Repo.all/2`, and `Repo.get/3` intentionally based on cardinality.
- Do not leak Repo-specific control flow into controllers or LiveViews.
