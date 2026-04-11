# ExUnit Patterns Reference

Source sample: `plugins/elixir-phoenix/skills/testing/references/exunit-patterns.md`

- Default to `async: true` unless the test mutates global state or uses shared mocks.
- Use setup chains to build readable test context and keep expensive setup out of individual assertions.
- Prefer pattern-matching assertions, `assert_receive`, and tagged subsets over sleeps and ambiguous checks.
- Keep DataCase and ConnCase responsible for sandbox ownership and common imports.
- Re-run flaky suites with the recorded seed to confirm state leakage before changing the code.
