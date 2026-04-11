# Channels and Presence Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/channels-presence.md`

- Use channels when the feature is a shared real-time topic, not just a single LiveView event loop.
- Authenticate joins with signed tokens or session-derived identity before tracking presence.
- Handle presence diffs incrementally instead of rebuilding the entire roster on every update.
- Keep subscription and tracking logic on the connected path only.
- Broadcast IDs and compact payloads; fetch full records from contexts when the LiveView needs them.
