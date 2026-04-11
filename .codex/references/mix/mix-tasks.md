# Mix Tasks

## Overview
Mix tasks automate common development tasks.

## Creating a Task
```elixir
defmodule Mix.Tasks.Hello do
  use Mix.Task

  @shortdoc "Says hello"
  @moduledoc """
  A simple hello task.
  
  Usage: mix hello [name]
  """

  @impl true
  def run(args) do
    name = List.first(args) || "World"
    Mix.shell().info("Hello, #{name}!")
  end
end
```

## Built-in Tasks
```bash
mix deps.get          # Get dependencies
mix compile           # Compile project
mix test              # Run tests
mix run               # Run code
mix format            # Format code
mix clean             # Remove build artifacts
```

## Task Naming
- Module: `Mix.Tasks.HelloWorld` → command: `mix hello.world`