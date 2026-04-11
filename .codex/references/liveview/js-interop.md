# JS Interop Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/js-interop.md`

- Wrap third-party DOM islands with `phx-update="ignore"` when the library owns the subtree.
- Keep LiveView hooks small and clean up listeners in `destroyed` so reconnects do not leak handlers.
- Prefer LiveView JS commands before custom hooks when the interaction is just show, hide, focus, or push.
- Rehydrate client widgets from assigns instead of hiding durable state only in browser memory.
- Treat hook IDs and DOM selectors as part of the LiveView contract and keep them stable.
