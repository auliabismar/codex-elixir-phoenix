# Security Headers Reference

Source sample: `plugins/elixir-phoenix/skills/security/references/security-headers.md`

- Keep `protect_from_forgery` and secure browser headers in the browser pipeline.
- Set CSP, frame, referrer, and content-type headers explicitly for production-facing apps.
- Treat cookie flags and TLS-only transport as part of the auth boundary, not optional hardening.
- Filter secrets from logs and error reports before they leave the app.
- Review header policy changes together with any feature that embeds third-party content or scripts.
