# PubSub and Navigation Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/pubsub-navigation.md`

- Subscribe to PubSub only after `connected?/1` returns true so disconnected mount does not double-subscribe.
- Use `patch` or `push_patch` for param changes in the same LiveView and `navigate` or `push_navigate` for a different LiveView in the same session.
- Use regular links or redirects when leaving the live session boundary.
- Scope PubSub topics to the resource or tenant so broadcasts stay targeted.
- Re-render after broadcasts in tests to assert the subscribed state change.
