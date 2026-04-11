# Ecto Constraints

## Key Points
- Mirror database constraints in the changeset so constraint errors become regular validation results.
- Use `unique_constraint/3`, `foreign_key_constraint/3`, and `check_constraint/3` after validations.
- Name custom constraints explicitly when the database name is not inferred.
