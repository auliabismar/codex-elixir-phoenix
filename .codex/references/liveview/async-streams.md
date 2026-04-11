# Async and Streams Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/async-streams.md`

- `mount/3` runs once for the disconnected HTTP render and again after WebSocket connect.
- Put expensive queries behind `assign_async/3` and extract needed values before the async closure so the socket is not copied.
- Use `stream/3`, `stream_insert/4`, and `stream_delete/3` for long lists to keep memory usage flat.
- Use CSS or stream-aware templates for empty states; a stream is not a regular enumerable assign.
- In tests, call `render_async/1` before asserting async-loaded content.
