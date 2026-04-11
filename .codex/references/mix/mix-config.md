# Mix Config

## Overview
Mix is Elixir's build tool and config manages application settings.

## Config Files
```elixir
# config/config.exs
import Config

config :my_app,
  ecto_repos: [MyApp.Repo],
  foo: :bar

config :my_app, MyApp.Endpoint,
  url: [host: "localhost"]
```

## Environment Specific
```elixir
# config/dev.exs
import Config

config :my_app, MyApp.Endpoint,
  http: [ip: {127, 0, 0, 1}, port: 4000],
  debug_errors: true

# config/prod.exs
import Config

config :my_app, MyApp.Endpoint,
  url: [host: "example.com"],
  cache_static_manifest: "priv/static/cache_manifest.json"
```

## Accessing Config
```elixir
Application.get_env(:my_app, :some_key)
Application.get_env(:my_app, :some_key, default)
```