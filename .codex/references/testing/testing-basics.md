# Testing Basics

## Overview
ExUnit is the built-in testing framework for Elixir.

## Basic Test
```elixir
defmodule MyApp.AccountsTest do
  use MyApp.DataCase, async: true

  describe "create_user/1" do
    test "creates user with valid data" do
      attrs = %{name: "Alice", email: "alice@example.com"}
      assert {:ok, user} = Accounts.create_user(attrs)
      assert user.name == "Alice"
    end

    test "returns error for invalid email" do
      attrs = %{name: "Bob", email: "invalid"}
      assert {:error, changeset} = Accounts.create_user(attrs)
      assert "is invalid" in errors_on(changeset).email
    end
  end
end
```

## Setup Callbacks
```elixir
setup do
  user = insert(:user)
  %{user: user}
end

test "does something", %{user: user} do
  assert user.name == "Test User"
end
```

## Key Assertions
- `assert` - Pass if expression is truthy
- `refute` - Pass if expression is falsy
- `assert_raise` - Expect exception
- `assert_receive` - Expect message