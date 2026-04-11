# Ecto Changesets

## Key Points
- Start with `cast/4`, then run validations, then constraints.
- Use `validate_required/3` for request-shape rules and `unique_constraint/3` for database-backed guarantees.
- Return the changeset instead of raising so callers can choose the control flow.
