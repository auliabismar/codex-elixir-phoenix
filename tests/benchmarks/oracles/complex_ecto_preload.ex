defmodule MyApp.Repo.Preloads do
  import Ecto.Query
  def preload_nested(query) do
    query |> preload([:user, posts: [:comments, :author]])
  end
end
