# Ecto Migrations

## Key Points
- Keep migrations additive and reversible whenever possible.
- Add indexes and constraints in the same migration that introduces the column when the database contract requires them.
- Use explicit `up/0` and `down/0` only when `change/0` cannot be reversed safely.

## Example
```elixir
def change do
  create table(:users) do
    add :email, :string, null: false
    timestamps()
  end

  create unique_index(:users, [:email])
end
```
