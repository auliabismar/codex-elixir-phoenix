# Forms and Uploads Reference

Source sample: `plugins/elixir-phoenix/skills/liveview-patterns/references/forms-uploads.md`

- Convert changesets with `to_form/1`, and set `changeset.action = :validate` when you want validation errors to render.
- Keep save handlers on the success-or-error tuple and reassign the returned form on error.
- Use `phx-debounce` or `phx-throttle` instead of hand-rolled timer logic in forms.
- Model nested collections with `inputs_for` plus explicit sort and drop params.
- Gate uploads with `allow_upload/3`, then consume entries explicitly in the submit flow.
