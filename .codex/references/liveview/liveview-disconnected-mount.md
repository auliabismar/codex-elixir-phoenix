# LiveView Disconnected Mount

## The Problem
When a LiveView first loads, it may need to handle the case where the user has no existing session.

## Pattern: Disconnected Mount

```elixir
def mount(params, session, socket) do
  socket =
    case LiveView.get_connect_info(socket, :user_id) do
      nil ->
        # User not authenticated - assign guest state
        assign(socket, 
          user: nil,
          status: :disconnected,
          redirect_to: "/login"
        )

      user_id ->
        # User is authenticated - load user data
        user = Accounts.get_user!(user_id)
        assign(socket, user: user, status: :connected)
    end

  {:ok, socket}
end
```

## Best Practices
1. Check authentication in `mount/3`
2. Use `on_mount` hooks for reusable logic
3. Return appropriate socket state for UI to respond
4. Use `redirect` in mount only with {:halt, socket}