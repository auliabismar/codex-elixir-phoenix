# Authentication Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/security/references/authentication.md`

- Prefer generated `phx.gen.auth` structure and keep password verification timing-safe.
- Do not leak whether the email or the password was wrong.
- Keep session cookies `http_only`, `secure`, and `same_site` configured deliberately.
- Load production secrets from `runtime.exs` and environment variables, not checked-in config.
- Redact passwords, tokens, and other sensitive fields from logs and struct inspection.
