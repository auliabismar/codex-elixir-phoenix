---
name: phx-review
description: Use when the user invokes $phx-review. Performs multi-agent semantic review of implemented changes.
---

# Phoenix Review

This skill handles the collaborative review of changes by multiple specialized agents.

## Instructions

1. Inspect the requested diff or changed files and identify correctness, regression, and acceptance risks.
2. Report findings ordered by severity with file references and recommended follow-up actions.

## Usage Examples

- `$phx-review "Review the current implementation diff"`
