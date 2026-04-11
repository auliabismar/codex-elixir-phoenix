# Ecto Preloads

## Key Points
- Preload associations before rendering or traversing them outside the context boundary.
- Avoid preloading everything by default; load only the associations needed for the use case.
- Prefer query-time preloads when filtering on association data.
