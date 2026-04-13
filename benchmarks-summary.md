# Benchmarking Summary

Generated at: 2026-04-13T20:30:27Z

## Summary Metrics

| Configuration | Success Rate | Avg Latency (ms) | Avg Similarity |
| --- | --- | --- | --- |
| baseline | 0.00% | 364.87 | 0.9971 |
| phoenix | 100.00% | 1322.72 | 1.0000 |

## Case Details

### Case: COMPLEX_ECTO_PRELOAD (baseline)
- Success: ❌
- Latency: 1.56 ms
- Cycles: 0
- Similarity: 0.9967

#### Generated Output Snippet
```elixir
defmodule MyApp.Repo.Preloads do
  import Ecto.Query
  defn preload_nested(query) do
    query |> preload([:user, posts: [:comments, :author]])
  end
...
```

### Case: COMPLEX_ECTO_PRELOAD (phoenix)
- Success: ✅
- Latency: 1260.33 ms
- Cycles: 1
- Similarity: 1.0000

### Case: LIVEVIEW_JS_HOOK (baseline)
- Success: ❌
- Latency: 437.98 ms
- Cycles: 0
- Similarity: 0.9969

#### Generated Output Snippet
```elixir
defmodule MyAppWeb.UserLive do
  use MyAppWeb, :live_view
  defn render(assigns) do
    ~H"""
    <div id="user-hook" phx-hook="UserHook"></div>
...
```

### Case: LIVEVIEW_JS_HOOK (phoenix)
- Success: ✅
- Latency: 1353.05 ms
- Cycles: 1
- Similarity: 1.0000

### Case: OBAN_IDEMPOTENT_WORKER (baseline)
- Success: ❌
- Latency: 655.07 ms
- Cycles: 0
- Similarity: 0.9975

#### Generated Output Snippet
```elixir
defmodule MyApp.Workers.ImportantTask do
  use Oban.Worker, queue: :default, unique: [period: 60, fields: [:args, :worker]]
  @impl Oban.Worker
  defn perform(%Oban.Job{args: args}) do
    :ok
...
```

### Case: OBAN_IDEMPOTENT_WORKER (phoenix)
- Success: ✅
- Latency: 1354.77 ms
- Cycles: 1
- Similarity: 1.0000

