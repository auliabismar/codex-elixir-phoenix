# LiveView Testing Reference

Source sample: `plugins/elixir-phoenix/skills/testing/references/liveview-testing.md`

- Mount LiveViews with `live/2`, then drive the DOM through `element/3`, `form/3`, `render_click/1`, and `render_submit/1`.
- For `assign_async` flows, call `render_async/1` before asserting loaded content.
- Use `assert_patch/2` and `assert_redirect/2` based on whether navigation stays inside the same LiveView.
- Test uploads with `file_input/4` and `render_upload/2` instead of bypassing LiveView upload plumbing.
- Broadcast to PubSub in the test and re-render the view to assert subscribed updates.
