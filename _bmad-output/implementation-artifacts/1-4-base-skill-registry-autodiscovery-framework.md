# Story 1.4: Base Skill Registry & Autodiscovery Framework

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a vibe-coder,
I want the plugin's skills to appear natively in my Codex prompt,
So that I can invoke them with `$phx-` commands seamlessly.

## Acceptance Criteria

1. **Given** the framework is loaded to the host
2. **When** Codex CLI searches for available tooling
3. **Then** it successfully discovers the plugins via YAML frontmatter description matching
4. **And** the baseline `SKILL.md` template is rigidly defined for all 41 command-based abilities moving forward.

## Tasks / Subtasks

- [ ] Create a template for `SKILL.md` that includes the required YAML frontmatter (e.g., `name`, `description`).
- [ ] Define the base directory structure for skills under `.codex/skills/`.
- [ ] Implement the first couple of base skills placeholders (e.g., `phx-plan`, `phx-work`, `phx-verify`, `phx-review`) with the `SKILL.md` template just to establish the autodiscovery framework functionality.
- [ ] Ensure the YAML frontmatter uses exact descriptions optimized for Codex auto-discovery so terms like `$phx-plan` trigger the right CLI behavior.

## Dev Notes

- **Architecture Compliance**:
  - **Skill Autodiscovery**: Codex CLI discovers skills natively directly via YAML frontmatter. Nothing else is needed. The `name` must be `kebab-case` starting with `phx-`.
  - **Directory Structure**: Each skill resides in its own folder: `.codex/skills/<skill-name>/SKILL.md`.
  - **Pattern Enforcement**: `SKILL.md` must adhere to a consistent structure (NFR19) containing YAML frontmatter and instructional markdown content.
  - **Naming Convention**: Codex assets use `kebab-case`.

- **Technical Requirements**:
  - You are NOT implementing the full logic of the 41 skills. You are establishing the registry directory structure and the template.
  - Set up folders like `.codex/skills/phx-plan/SKILL.md`, `.codex/skills/phx-work/SKILL.md`, `.codex/skills/phx-verify/SKILL.md`, `.codex/skills/phx-review/SKILL.md`.
  - Add highly targeted descriptions in the YAML frontmatter for these placeholders, e.g., "Use when the user invokes $phx-plan" or "Executes the plan step-by-step".

- **Previous Story Intelligence (from 1.3 & 1.2)**:
  - We've been building inside the `.codex/` distributed payload. 
  - Ensure all new files are under `.codex/skills/` without relying on external configurations since setup and session validation already handle the boot process.

### Project Structure Notes

- Alignment with unified project structure:
  - File generation must be restricted to `.codex/skills/`

### References

- [Source: planning-artifacts/epics.md#Story 1.4: Base Skill Registry & Autodiscovery Framework](file:///c:/projects/codex-elixir-phoenix/_bmad-output/planning-artifacts/epics.md)
- [Source: planning-artifacts/prd.md#Skill System](file:///c:/projects/codex-elixir-phoenix/_bmad-output/planning-artifacts/prd.md)
- [Source: planning-artifacts/architecture.md#Architectural Boundaries](file:///c:/projects/codex-elixir-phoenix/_bmad-output/planning-artifacts/architecture.md)

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log

### Completion Notes
- Ultimate context engine analysis completed - comprehensive developer guide created.

### File List

- `.codex/skills/SKILL_TEMPLATE.md`
- `.codex/skills/phx-plan/SKILL.md`
- `.codex/skills/phx-work/SKILL.md`
- `.codex/skills/phx-verify/SKILL.md`
- `.codex/skills/phx-review/SKILL.md`
