# Ecto Schema Basics

## Key Points
- Declare persisted fields inside `schema/2` and add `timestamps()` when the table stores them.
- Keep virtual input fields explicit with `virtual: true`.
- Separate schema declarations from query and business logic.

## Example
```elixir
schema "users" do
  field :email, :string
  field :name, :string
  field :password, :string, virtual: true
  timestamps()
end
```
