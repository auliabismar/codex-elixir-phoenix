# Ecto Query Composition

## Key Points
- Compose queries with small functions that accept and return a queryable.
- Keep optional filters branchless by applying them only when params are present.
- Prefer named bindings when several joins target the same table.
