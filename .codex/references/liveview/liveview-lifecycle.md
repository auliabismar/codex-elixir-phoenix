# LiveView Lifecycle

## Overview
LiveView is a real-time web framework built on top of Phoenix.

## Lifecycle Callbacks

```elixir
defmodule MyAppWeb.UserLive do
  use MyAppWeb, :live_view

  # Called when LiveView is first mounted
  def mount(params, session, socket) do
    {:ok, socket}
  end

  # Called before render, useful for redirects
  def mount(_params, _session, socket) do
    {:ok, assign(socket, count: 0)}
  end

  # Called when LiveView disconnects
  def terminate(_reason, socket) do
    # Cleanup
  end
end
```

## Key Functions
- `mount/3` - Initialize the LiveView
- `render/1` - Return the template (usually in heex)
- `handle_event/3` - Handle user actions
- `handle_info/2` - Handle internal messages
- `handle_params/3` - Handle URL params changes