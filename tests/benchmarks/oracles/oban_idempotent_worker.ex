defmodule MyApp.Workers.ImportantTask do
  use Oban.Worker, queue: :default, unique: [period: 60, fields: [:args, :worker]]
  @impl Oban.Worker
  def perform(%Oban.Job{args: args}) do
    :ok
  end
end
