# Code Organization

## Key Points
- Keep domain code under `lib/my_app/` and web-facing code under `lib/my_app_web/`.
- Prefer full module declarations like `defmodule MyApp.Accounts.User do` instead of nested `module` blocks.
- Store tests in matching folders so call sites and coverage stay easy to find.

## Typical Layout
```text
lib/
  my_app/
    accounts/
      user.ex
    repo.ex
  my_app_web/
    controllers/
    live/
    components/
    router.ex
test/
  my_app/
  my_app_web/
  support/
```
