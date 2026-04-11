# API Rate Limits

## Key Points
- Apply limits per credential or actor, not just per IP.
- Return `429` with a retry hint when throttling.
- Log limit breaches separately from normal validation failures.
