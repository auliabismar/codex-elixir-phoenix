# API Idempotency

## Key Points
- Require an idempotency key on retried write endpoints.
- Persist the key near the side effect so duplicate requests reuse the same result.
- Expire stored keys only after the client retry window has passed.
