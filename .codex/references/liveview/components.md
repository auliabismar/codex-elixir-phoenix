# Components Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/components.md`

- Prefer function components for reusable UI with `attr`, `slot`, and `:global` assigns.
- Reach for `LiveComponent` only when the component owns local state and targeted events.
- When a LiveComponent changes shared state, notify the parent instead of mutating competing copies.
- Use JS commands for focus, toggles, and loading states that do not need a server round trip.
- Colocated hooks are the upstream pattern for small hook-specific client behavior in LiveView 1.1+.
