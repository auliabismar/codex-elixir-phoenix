# OTP GenServer

## Overview
GenServer is the standard behavior for building concurrent servers in OTP.

## Basic GenServer
```elixir
defmodule MyApp.Cache do
  use GenServer

  def start_link(opts \\ []) do
    GenServer.start_link(__MODULE__, opts, name: __MODULE__)
  end

  @impl true
  def init(_opts) do
    {:ok, %{}}
  end

  @impl true
  def handle_call(:get_all, _from, state) do
    {:reply, state, state}
  end

  def get_all, do: GenServer.call(__MODULE__, :get_all)
end
```

## Callbacks
- `init/1` - Initialize state
- `handle_call/3` - Synchronous requests
- `handle_cast/2` - Async requests
- `handle_info/2` - Internal messages

## State Management
```elixir
def handle_call({:put, key, value}, _from, state) do
  new_state = Map.put(state, key, value)
  {:reply, value, new_state}
end
```