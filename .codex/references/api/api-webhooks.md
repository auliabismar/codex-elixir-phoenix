# API Webhooks

## Key Points
- Sign webhook payloads and verify signatures before parsing business data.
- Make webhook handlers idempotent because providers retry aggressively.
- Return fast acknowledgements and move slow processing to background jobs.
