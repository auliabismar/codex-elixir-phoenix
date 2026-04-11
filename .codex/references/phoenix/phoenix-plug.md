# Phoenix Plug

## Overview
Plugs are composable modules that transform connections.

## Writing a Plug
```elixir
defmodule MyAppWeb.Plugs.Authentication do
  import Plug.Conn

  def init(opts), do: opts

  def call(conn, _opts) do
    case get_session(conn, :user_id) do
      nil ->
        conn
        |> halt()
        |> redirect(to: "/login")

      user_id ->
        assign(conn, :current_user, Repo.get(User, user_id))
    end
  end
end
```

## Using in Router
```elixir
pipeline :browser do
  plug :accepts, ["html"]
  plug :fetch_session
  plug MyAppWeb.Plugs.Authentication
end
```

## Plug Functions
- `halt/1` - Stop the plug pipeline
- `assign/3` - Add to assigns
- `put_session/3` - Set session value