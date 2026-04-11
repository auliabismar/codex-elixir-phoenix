# API Serialization

## Key Points
- Serialize through plain maps so response contracts stay readable in tests.
- Prefer `DateTime.to_iso8601/1` and string keys only when the external contract requires them.
- Use `Jason.encode!/1` on the final map or list rather than encoding each item separately.

## Example
```elixir
def to_api_map(user) do
  %{
    id: user.id,
    email: user.email,
    inserted_at: DateTime.to_iso8601(user.inserted_at)
  }
end

Jason.encode!(%{data: Enum.map(users, &to_api_map/1)})
```
