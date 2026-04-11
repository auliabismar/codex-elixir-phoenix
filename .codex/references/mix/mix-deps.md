# Mix Dependencies

## Overview
Dependencies are managed in mix.exs.

## Specifying Deps
```elixir
def deps do
  [
    {:ecto, "~> 3.0"},
    {:phoenix, "~> 1.6"},
    {:oban, "~> 2.0"},
    {:jason, ">= 1.0.0"},
    {:plug_cowboy, "~> 2.0", runtime: false}
  ]
end
```

## Deps Options
- `:runtime` - Include in prod (default true)
- `:only` - Environments to include
- `:override` - Override transitive deps
- `:git` / `:github` - Git sources

## Managing Deps
```bash
mix deps.get          # Install
mix deps.update phx   # Update specific
mix deps.clean --unlock  # Remove lock
mix deps.tree         # Show tree
```