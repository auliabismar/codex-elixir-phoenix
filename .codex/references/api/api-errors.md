# API Errors

## Key Points
- Use one error envelope shape across the API.
- Include a stable machine code plus a human-readable message.
- Map validation failures to `422` and unexpected failures to `500`.
