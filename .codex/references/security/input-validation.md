# Input Validation Reference

Source sample: `plugins/elixir-phoenix/skills/security/references/input-validation.md`

- Validate all user and API input through changesets or equivalent typed boundaries.
- Never turn user input into atoms with `String.to_atom/1`; use `to_existing_atom/1` only when unavoidable.
- Validate file uploads by extension, content type, and size before persistence.
- Use safe path helpers when joining user-controlled file paths to avoid traversal bugs.
- Escape or sanitize untrusted rich text instead of rendering it raw.
