# Testing Mocks

## Overview
Mocking in Elixir should be used sparingly. Prefer real implementations when possible.

## When to Mock
- External APIs
- Slow operations
- Non-deterministic behavior

## Using Mox
```elixir
# In test_helper.exs
Mox.defmock(MyApp.MockService, for: MyApp.ServiceBehaviour)

# In test
setup :set_mox_from_context
setup :verify_on_exit!

test "calls external service" do
  expect(MyApp.MockService, :process, fn _ -> {:ok, "response"} end)
  
  result = MyApp.process_data(%{data: "test"})
  
  assert result == {:ok, "response"}
end
```

## Anti-Patterns
- Mocking everything
- Mocking the database (use sandbox)
- Complex mock setup

## Alternative: Bypass
```elixir
defp bypass_external_api do
  Bypass.open()
end
```