# Testing Contexts

## Overview
Contexts organize related functionality and tests.

## Context Pattern
```elixir
defmodule MyApp.AccountsTest do
  use MyApp.DataCase, async: true

  alias MyApp.Accounts

  describe "list_users/0" do
    test "returns all users" do
      insert(:user, name: "Alice")
      insert(:user, name: "Bob")
      
      assert length(Accounts.list_users()) == 2
    end
    
    test "returns empty list when no users" do
      assert Accounts.list_users() == []
    end
  end
  
  describe "get_user!/1" do
    test "raises for invalid id" do
      assert_raise Ecto.NoResultsError, fn ->
        Accounts.get_user!(999999)
      end
    end
  end
end
```

## Best Practices
1. Use `describe` blocks to group by function
2. Use `test` with clear names
3. Factory pattern for test data
4. Test success AND failure cases