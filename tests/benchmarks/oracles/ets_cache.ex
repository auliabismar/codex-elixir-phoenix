defmodule MyApp.ETS do
  def start_link(opts) do
    name = Keyword.get(opts, :name, __MODULE__)
    :ets.new(name, [:set, :named_table, :public, read_concurrency: true])
    Agent.start_link(fn -> :ets.new(name, [:set, :named_table]) end, name: name)
  end

  def get(key) do
    case :ets.lookup(__MODULE__, key) do
      [{^key, value}] -> {:ok, value}
      [] -> {:error, :not_found}
    end
  end

  def put(key, value) do
    :ets.insert(__MODULE__, {key, value})
    :ok
  end
end