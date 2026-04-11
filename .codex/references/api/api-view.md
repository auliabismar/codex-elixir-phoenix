# API View

## Key Points
- In modern Phoenix apps, prefer `MyAppWeb.UserJSON` style modules over legacy `:view` modules.
- Keep a small `data/1` helper per resource so list and show actions share one shape.
- Do not rely on controller assigns inside the serializer.

## Example
```elixir
defmodule MyAppWeb.UserJSON do
  def show(%{user: user}) do
    %{data: data(user)}
  end

  def index(%{users: users}) do
    %{data: Enum.map(users, &data/1)}
  end

  defp data(user), do: %{id: user.id, email: user.email}
end
```

## Content Types
- `application/json` for standard JSON APIs
- `application/problem+json` for machine-readable error payloads
