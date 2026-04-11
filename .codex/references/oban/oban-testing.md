# Oban Testing

## Overview
Testing Oban workers requires handling the async nature of job processing.

## Testing Workers
```elixir
defmodule MyApp.Workers.NotifyUserTest do
  use MyApp.DataCase, async: true

  test "sends email notification" do
    user = insert(:user, email: "test@example.com")
    
    Oban.insert!(MyApp.Workers.NotifyUser.new(%{
      "user_id" => user.id,
      "message" => "Hello!"
    }))
    
    assert_enqueued(worker: MyApp.Workers.NotifyUser)
    
    perform_job(MyApp.Workers.NotifyUser, %{
      "user_id" => user.id,
      "message" => "Hello!"
    })
    
    assert_email_sent(to: "test@example.com")
  end
end
```

## Testing Helpers
- `perform_job/2` - Run job synchronously
- `assert_enqueued/1` - Verify job was queued
- `refute_enqueued/1` - Verify job was NOT queued
- `toggle_enabled/1` - Enable/disable queue