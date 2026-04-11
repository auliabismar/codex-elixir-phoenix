# Oban Pro Basics Reference

Source sample: `plugins/elixir-phoenix/skills/oban/references/oban-pro-basics.md`

- Detect Pro usage before applying patterns: `Oban.Pro.Worker` and related modules change the API surface.
- Pro workers use `process/1` instead of the standard `perform/1` callback.
- Keep testing imports aligned with the installed package so OSS helpers are not mixed with Pro helpers.
- Treat workflows, batches, and encrypted workers as distinct patterns instead of assuming the OSS defaults.
- If the repo does not depend on Oban Pro, do not introduce Pro-specific examples or modules.
