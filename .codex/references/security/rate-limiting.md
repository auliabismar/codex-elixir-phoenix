# Rate Limiting Reference

Source sample: `plugins/elixir-phoenix/skills/security/references/rate-limiting.md`

- Rate limit by a composite identity such as user, IP, route, or action depending on the abuse model.
- Apply separate limits for browser traffic, API tokens, and auth endpoints.
- Keep throttling state outside the request process so limits survive retries and parallel requests.
- Return predictable retry semantics and telemetry so abuse controls can be tuned safely.
- Coordinate inbound rate limits with outbound job queues when the app fans out to external APIs.
