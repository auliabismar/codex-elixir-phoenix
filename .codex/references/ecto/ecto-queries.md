# Ecto Queries

## Key Points
- Build queries with `from/2` or the pipeable query API.
- Keep filtering and ordering inside query functions so callers do not rebuild business rules.
- Return queries from contexts when further composition is expected.
