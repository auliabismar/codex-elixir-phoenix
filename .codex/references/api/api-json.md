# API JSON

## Key Points
- Use `json/2` for small responses or `render/3` into a dedicated `*JSON` module for stable response shapes.
- Convert structs into plain maps before encoding so the wire format stays explicit.
- Keep top-level envelopes consistent across endpoints.

## Example
```elixir
def show(conn, %{"id" => id}) do
  user = Accounts.get_user!(id)

  json(conn, %{
    data: %{
      id: user.id,
      email: user.email
    }
  })
end
```
