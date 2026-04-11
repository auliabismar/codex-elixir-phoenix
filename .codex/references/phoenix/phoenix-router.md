# Phoenix Router

## Overview
Routes map URLs to controllers and LiveViews.

## Basic Router
```elixir
defmodule MyAppWeb.Router do
  use MyAppWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  scope "/", MyAppWeb do
    pipe_through :browser
    
    get "/", PageController, :home
    resources "/users", UserController
    
    live "/users/:id/edit", UserLive.Edit
  end

  scope "/api", MyAppWeb do
    pipe_through :api
    resources "/posts", PostController, only: [:index, :show]
  end
end
```

## Scope Options
- `pipe_through` - Apply pipeline
- `resources` - RESTful routes
- `live` - LiveView routes
- `get/put/post/delete` - Individual routes