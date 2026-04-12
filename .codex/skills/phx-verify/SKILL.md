---
name: phx-verify
description: Use when the user invokes $phx-verify. Run Elixir compilation and formatting checks on the host machine.
---

# Phoenix Verify

This skill allows the framework to execute native Elixir tooling (Mix) to verify the current state of the project. It ensures that the code compiles without warnings and follows the project's formatting rules.

## Instructions

1.  **Execute Documentation**:
    - Use `validate_compilation.validate_project(repo_root)` hook to run the verification suite.
    - This will execute:
        1. `mix compile --warnings-as-errors`
        2. `mix format --check-formatted`

2.  **Handle Results**:
    - If `success` is `true`, report that the project is healthy and passes all checks.
    - If `success` is `false`, extract the `logs` and `error_type` and present them to the user.
    - Treat `error_type: toolchain` as an environment/setup failure, not an application compile regression.
    - Subsequent actions should prioritize fixing the reported errors or warnings.

3.  **Autonomous Correction**:
    - If this skill was triggered as a post-task verification (e.g., after `$phx-work`), failed logs MUST be used as context for an immediate self-correction attempt.

## Usage Examples

- `$phx-verify`: Runs the full verification suite on the current project.
