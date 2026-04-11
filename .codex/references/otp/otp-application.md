# OTP Application

## Overview
Applications are the unit of deployment in Elixir/OTP.

## Application Module
```elixir
defmodule MyApp.Application do
  @impl true
  def start(_type, _args) do
    children = [
      MyApp.Repo,
      MyApp.Endpoint,
      {Registry, keys: :unique, name: MyApp.Registry},
      {DynamicSupervisor, strategy: :one_for_one}
    ]

    opts = [strategy: :one_for_one, name: MyApp.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
```

## Application Callback
```elixir
@impl true
def start(_type, _args) do
  # Return {:ok, pid} or {:error, reason}
end
```

## mix.exs Configuration
```elixir
def application do
  [
    extra_applications: [:logger],
    mod: {MyApp.Application, []}
  ]
end
```