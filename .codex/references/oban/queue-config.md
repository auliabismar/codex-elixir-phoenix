# Queue Configuration Reference

Source sample: `plugins/elixir-phoenix/skills/oban/references/queue-config.md`

- Separate I/O-heavy, CPU-heavy, and externally rate-limited jobs into different queues.
- Size the Repo pool to cover queue concurrency plus a safety buffer.
- Use queue-level `dispatch_cooldown` when a downstream API needs rate limiting.
- Enable housekeeping plugins such as pruner and stuck-job recovery in production.
- Treat cron configuration as operational code and keep schedule ownership explicit.
