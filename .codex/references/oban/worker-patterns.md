# Worker Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/oban/references/worker-patterns.md`

- Jobs must be idempotent and should carry IDs or small primitive args, not loaded structs.
- Pattern match job args with string keys because Oban serializes JSON payloads.
- Use worker options deliberately for queue, attempts, priority, uniqueness, and timeout.
- Handle all job outcomes explicitly, including `:ok`, `{:error, reason}`, `{:cancel, reason}`, and `{:snooze, delay}`.
- Attach telemetry for failed jobs so production retries are observable.
