# Ecto Multi

## Key Points
- Use `Ecto.Multi` when several Repo operations must succeed or fail together.
- Name each step clearly so failed transactions are easy to debug.
- Keep external side effects outside the database transaction when possible.
