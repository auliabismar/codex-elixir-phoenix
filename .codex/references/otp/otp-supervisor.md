# OTP Supervisor

## Overview
Supervisors manage child processes and handle failures.

## Dynamic Supervisor
```elixir
defmodule MyApp.DynamicSupervisor do
  use DynamicSupervisor

  def start_link(opts \\ []) do
    DynamicSupervisor.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(_opts) do
    DynamicSupervisor.init(strategy: :one_for_one)
  end

  def start_child(spec) do
    DynamicSupervisor.start_child(__MODULE__, spec)
  end
end
```

## Strategies
- `:one_for_one` - Restart only failed child
- `:one_for_all` - Restart all children
- `:rest_for_one` - Restart younger siblings

## Supervisor Spec
```elixir
worker(MyApp.Worker, [arg1, arg2])
```