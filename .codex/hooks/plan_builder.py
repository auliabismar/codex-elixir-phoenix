"""
plan_builder.py — Helper for creating new markdown plans in .codex/plans/{slug}/plan.md.

This module provides deterministic slug normalization and plan file creation using
the canonical _template/plan.md scaffold.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Words to strip from the beginning of a feature request to create a concise slug.
_IMPERATIVE_VERBS = {
    "create", "add", "implement", "build", "make", "generate", "new", "setup",
    "start", "begin", "init", "initialize", "develop", "provide", "fix", "update",
    "change", "refactor", "delete", "remove"
}
_ARTICLES_AND_CONJUNCTIONS = {"a", "an", "the", "for", "with", "to", "and", "of", "in", "just"}

_STRIP_WORDS = _IMPERATIVE_VERBS | _ARTICLES_AND_CONJUNCTIONS
_WINDOWS_RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9",
}
_VALID_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TASKS_SECTION_RE = re.compile(r"(?ms)^## Tasks\s*\n\n.*?(?=^## Notes\s*$)")
_GOAL_PLACEHOLDER = "{Describe what this plan aims to accomplish in one or two sentences.}"
_NOTES_PLACEHOLDER = "{Optional: additional context, references, or constraints that the agent should be aware of.}"


def _validate_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not slug:
        raise ValueError("Unable to derive a non-empty plan slug.")
    if not _VALID_SLUG_RE.fullmatch(slug):
        raise ValueError(f"Slug {slug!r} must be kebab-case ASCII.")
    if slug in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"Slug {slug!r} is reserved on Windows.")
    return slug


def normalize_slug(text: str) -> str:
    """Resolve a feature request text into a concise kebab-case slug.

    Example:
        "Create an invoice PDF generator" -> "invoice-pdf-generator"
    """
    words = re.sub(r"[^a-z0-9]+", " ", text.lower()).split()
    while words and words[0] in _STRIP_WORDS:
        words.pop(0)
    return _validate_slug("-".join(words))


def create_plan_file(repo_root: Path, slug: str, goal: str, tasks: list[str], notes: str = "") -> Path:
    """Create a new plan file from the template.

    Args:
        repo_root: Root of the repository.
        slug: The normalized slug for the feature.
        goal: Brief description of the goal.
        tasks: List of task descriptions (without the "- [ ] " prefix).
        notes: Optional additional notes.
        
    Returns:
        Path to the created plan.md file.
        
    Raises:
        FileExistsError: If the plan already exists.
        FileNotFoundError: If the template is missing.
    """
    slug = _validate_slug(slug)
    plan_dir = repo_root / ".codex" / "plans" / slug
    plan_path = plan_dir / "plan.md"
    template_path = repo_root / ".codex" / "plans" / "_template" / "plan.md"

    if not template_path.exists():
        raise FileNotFoundError(f"Template missing at {template_path}")

    cleaned_tasks = [task.strip() for task in tasks if task.strip()]
    if not cleaned_tasks:
        raise ValueError("tasks must include at least one non-empty item")

    template_content = template_path.read_text(encoding="utf-8")
    content = template_content.replace("{slug}", slug)
    content = content.replace(_GOAL_PLACEHOLDER, goal)

    task_lines = [f"- [ ] {task}" for task in cleaned_tasks]
    task_block = "\n".join(task_lines)
    content, replaced = _TASKS_SECTION_RE.subn(f"## Tasks\n\n{task_block}\n\n", content, count=1)
    if replaced != 1:
        raise ValueError("Template is missing a canonical ## Tasks section followed by ## Notes.")

    content = content.replace(_NOTES_PLACEHOLDER, notes or "N/A")
    if any(placeholder in content for placeholder in (_GOAL_PLACEHOLDER, _NOTES_PLACEHOLDER)):
        raise ValueError("Template placeholders were not fully replaced.")

    plan_dir.mkdir(parents=True, exist_ok=True)

    with plan_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)

    return plan_path
