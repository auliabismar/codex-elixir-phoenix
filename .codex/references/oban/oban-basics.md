# Oban Basics

## Overview
Oban is a robust job processing library for Elixir.

## Worker Definition
```elixir
defmodule MyApp.Workers.NotifyUser do
  use Oban.Worker

  @impl true
  def perform(%{"user_id" => user_id, "message" => message}) do
    user = Repo.get!(User, user_id)
    Email.send(user.email, message)
    :ok
  end
end
```

## Enqueueing Jobs
```elixir
# Basic
MyApp.Workers.NotifyUser.new(%{user_id: 123, message: "Hi!"})
|> Oban.insert()

# With options
MyApp.Workers.NotifyUser.new(%{user_id: 123}, scheduled_at: ~U[2024-01-01 12:00:00Z])
|> Oban.insert()
```

## Key Options
- `priority` - 0 (highest) to 9 (lowest)
- `max_attempts` - Retry limit
- `schedule` - Cron syntax
- `unique` - Prevent duplicates