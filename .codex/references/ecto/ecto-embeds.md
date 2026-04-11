# Ecto Embeds

## Key Points
- Use embeds for nested document-shaped data that does not need its own table.
- Validate nested payloads with `cast_embed/3`.
- Keep embedded schemas small and versionable because migrations do not manage their structure.
