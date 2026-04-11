# Context Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/phoenix-contexts/references/context-patterns.md`

- Keep business logic in contexts and keep controllers and LiveViews thin.
- Make the scope or authorization context the first argument to public context functions.
- Use `Ecto.Multi` for multi-step writes and side effects such as welcome emails or PubSub broadcasts.
- Cross context boundaries through public APIs or explicit foreign keys; do not reach into another context's internals through raw `Repo` queries.
- Use a fallback controller for consistent API error translation.
