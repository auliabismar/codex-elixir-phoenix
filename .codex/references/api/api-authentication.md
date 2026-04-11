# API Authentication

## Key Points
- Authenticate at the boundary with plugs or verified tokens before controller logic runs.
- Keep bearer-token parsing and authorization checks separate.
- Return `401` for missing credentials and `403` for denied access.
