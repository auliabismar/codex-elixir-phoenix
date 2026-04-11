# Oban Testing Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/oban/references/testing-patterns.md`

- Configure Oban test mode explicitly with `testing: :manual` or `testing: :inline`.
- Assert enqueued jobs with worker, args, queue, and schedule expectations instead of counting rows manually.
- Use `perform_job/2` for focused worker behavior and `Oban.drain_queue/1` for end-to-end queue flows.
- Keep idempotency and uniqueness in place for user-triggered jobs even in tests.
- Put references such as file paths or IDs in job args; avoid large payload blobs.
