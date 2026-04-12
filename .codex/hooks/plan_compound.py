"""
plan_compound.py -- Orchestration helper for feature compounding and learning extraction.
"""

from collections.abc import Mapping, Sequence
import subprocess
from datetime import datetime
from pathlib import Path

import plan_state
import plan_work


class AmbiguityError(Exception):
    """Raised when multiple eligible plans exist and no target was specified."""

    pass


_INCLUDED_IGNORED_SUFFIXES = {
    ".css",
    ".ex",
    ".exs",
    ".heex",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".leex",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
_EXCLUDED_ADDED_PREFIXES = {
    ".git",
    ".pytest_cache",
    ".tmp-manual-verify",
    ".tmp-tests",
    ".venv",
    "_bmad-output",
    "blob-report",
    "build",
    "dist",
    "node_modules",
    "playwright-report",
    "scratch",
    "test-results",
}
_EXCLUDED_ADDED_PATHS = {
    ".codex/agent-memory",
    ".codex/plans",
}
_SOURCE_DIFF_BASIS = "git diff HEAD plus added untracked source files"


def resolve_target_plan(repo_root: Path, target: str | Path | None = None) -> Path:
    """Find the target plan.md in .codex/plans/."""
    repo_root = repo_root.resolve()
    plans_dir = repo_root / ".codex" / "plans"

    if target is not None:
        return _require_completed_plan(_resolve_explicit_plan(repo_root, plans_dir, target))

    if not plans_dir.exists():
        raise FileNotFoundError(f"Plans directory missing at {plans_dir}")

    eligible_plans = []
    for entry in sorted(plans_dir.iterdir(), key=lambda path: path.name):
        if not entry.is_dir() or entry.name == "_template":
            continue

        plan_path = entry / "plan.md"
        if not plan_path.exists() or not _is_completed_plan(plan_path):
            continue

        eligible_plans.append(plan_path)

    if not eligible_plans:
        raise FileNotFoundError(
            "No completed plans found in .codex/plans/. "
            "Ensure at least one plan has recognized tasks and all are marked [x]."
        )

    if len(eligible_plans) > 1:
        slugs = sorted([p.parent.name for p in eligible_plans])
        raise AmbiguityError(
            f"Multiple completed plans found: {', '.join(slugs)}. "
            "Please specify which one to compound: $phx-compound <slug>"
        )

    return eligible_plans[0]


def get_analysis_packet(plan_path: Path) -> dict:
    """Gather plan context and git diff for the analytics agent."""
    plan_path = _require_completed_plan(Path(plan_path).resolve())
    repo_root = _find_repo_root(plan_path)
    context = plan_work.get_work_context(plan_path)
    git_diff = _collect_git_diff(repo_root)

    return {
        "slug": plan_path.parent.name,
        "plan_path": str(plan_path),
        "plan_content": plan_path.read_text(encoding="utf-8"),
        "goal": context["goal"],
        "notes": context["notes"],
        "completed_tasks": context["completed_tasks"],
        "pending_task": context["task"],
        "complete": context["complete"],
        "git_diff": git_diff,
        "source_diff_basis": _SOURCE_DIFF_BASIS,
        "repo_root": str(repo_root),
    }


def persist_learning(
    repo_root: Path,
    slug: str,
    learning: Mapping[str, object] | str,
) -> Path:
    """Save deduced learnings into .codex/agent-memory/{slug}.md."""
    repo_root = Path(repo_root).resolve()
    memory_dir = (repo_root / ".codex" / "agent-memory").resolve()
    memory_dir.mkdir(parents=True, exist_ok=True)

    safe_slug = _sanitize_slug(slug)
    memory_file = (memory_dir / f"{safe_slug}.md").resolve()
    if not _is_relative_to(memory_file, memory_dir):
        raise ValueError(f"Refusing to write outside agent memory: {memory_file}")

    payload = _normalize_learning_payload(learning)
    section = _render_learning_section(payload)

    if memory_file.exists():
        existing = memory_file.read_text(encoding="utf-8")
        memory_file.write_text(existing.rstrip() + "\n\n" + section + "\n", encoding="utf-8")
    else:
        memory_file.write_text(
            f"# Agent Memory: {safe_slug}\n\n{section}\n",
            encoding="utf-8",
        )

    return memory_file


def _resolve_explicit_plan(repo_root: Path, plans_dir: Path, target: str | Path) -> Path:
    raw_target = str(target).strip()
    if not raw_target:
        raise FileNotFoundError("Plan target is empty.")

    plans_root = plans_dir.resolve()
    target_path = Path(raw_target)

    candidates = []
    if target_path.is_absolute():
        candidates.append(target_path)
    elif len(target_path.parts) == 1 and target_path.suffix != ".md":
        candidates.append(plans_dir / target_path / "plan.md")
    else:
        candidates.append(repo_root / target_path)
        candidates.append(plans_dir / target_path)

    first_inside_path = None
    for candidate in candidates:
        resolved = _normalize_plan_candidate(candidate)
        if not _is_relative_to(resolved, plans_root):
            continue

        relative_path = resolved.relative_to(plans_root)
        if (
            not relative_path.parts
            or relative_path.parts[0] == "_template"
            or resolved.name != "plan.md"
        ):
            continue

        if first_inside_path is None:
            first_inside_path = resolved

        if resolved.exists():
            return resolved

    missing_path = first_inside_path or _normalize_plan_candidate(candidates[0])
    raise FileNotFoundError(f"Plan '{raw_target}' not found at {missing_path}")


def _normalize_plan_candidate(candidate: Path) -> Path:
    if candidate.suffix != ".md":
        candidate = candidate / "plan.md"
    return candidate.resolve()


def _is_completed_plan(plan_path: Path) -> bool:
    tasks = plan_state.load_tasks(plan_path)
    return bool(tasks) and all(task["done"] for task in tasks)


def _require_completed_plan(plan_path: Path) -> Path:
    tasks = plan_state.load_tasks(plan_path)
    if not tasks:
        raise ValueError(
            f"Plan '{plan_path}' has no recognized tasks in the ## Tasks section."
        )
    if not all(task["done"] for task in tasks):
        raise ValueError(
            f"Plan '{plan_path}' is not complete. Compound only supports completed plans."
        )
    return plan_path


def _collect_git_diff(repo_root: Path) -> str:
    tracked_diff = _run_git(repo_root, "diff", "HEAD")
    added_diffs = [
        _diff_added_file(repo_root, rel_path)
        for rel_path in _list_added_source_files(repo_root)
    ]

    parts = [part.strip() for part in [tracked_diff, *added_diffs] if part.strip()]
    if not parts:
        raise ValueError(
            "No meaningful diff found to analyze. "
            "Ensure your implementation changes exist in the working tree."
        )
    return "\n\n".join(parts)


def _list_added_source_files(repo_root: Path) -> list[str]:
    status_output = _run_git(
        repo_root,
        "status",
        "--porcelain=v1",
        "-z",
        "--ignored=matching",
        "--untracked-files=all",
    )

    paths: list[str] = []
    for entry in status_output.split("\0"):
        if not entry:
            continue

        status = entry[:2]
        if status not in {"??", "!!"}:
            continue

        rel_path = Path(entry[3:])
        if _is_excluded_added_path(rel_path):
            continue

        abs_path = (repo_root / rel_path).resolve()
        if not abs_path.is_file():
            continue

        if status == "!!" and abs_path.suffix.lower() not in _INCLUDED_IGNORED_SUFFIXES:
            continue

        paths.append(rel_path.as_posix())

    return sorted(set(paths))


def _is_excluded_added_path(rel_path: Path) -> bool:
    rel_posix = rel_path.as_posix()
    parts = rel_path.parts
    if parts and parts[0] in _EXCLUDED_ADDED_PREFIXES:
        return True
    return any(
        rel_posix == prefix or rel_posix.startswith(f"{prefix}/")
        for prefix in _EXCLUDED_ADDED_PATHS
    )


def _diff_added_file(repo_root: Path, rel_path: str) -> str:
    proc = subprocess.run(
        ["git", "diff", "--no-index", "--", "/dev/null", rel_path],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if proc.returncode not in {0, 1}:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown git error"
        raise ValueError(f"Unable to diff added file '{rel_path}': {detail}")
    return proc.stdout.strip()


def _run_git(repo_root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError("Git is required to compound learnings in this repository.") from exc
    except OSError as exc:
        raise ValueError(f"Unable to access git repository at {repo_root}: {exc}") from exc

    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown git error"
        raise ValueError(f"Git {' '.join(args)} failed: {detail}")

    return proc.stdout


def _find_repo_root(start_path: Path) -> Path:
    """Walk up until .git is found."""
    curr = start_path.resolve()
    if curr.is_file():
        curr = curr.parent

    for parent in [curr] + list(curr.parents):
        if (parent / ".git").exists():
            return parent

    raise FileNotFoundError(f"Git repository not found for {start_path}")


def _sanitize_slug(slug: str) -> str:
    raw_slug = slug.strip()
    if not raw_slug:
        raise ValueError("Memory slug is empty.")
    if "/" in raw_slug or "\\" in raw_slug:
        raise ValueError(f"Memory slug must not contain path separators: {raw_slug}")
    if Path(raw_slug).is_absolute() or raw_slug in {".", ".."} or ":" in raw_slug:
        raise ValueError(f"Memory slug must be a plain filename stem: {raw_slug}")
    return raw_slug


def _normalize_learning_payload(learning: Mapping[str, object] | str) -> dict[str, object]:
    if isinstance(learning, str):
        notes = learning.strip()
        return {
            "source_plan": "N/A",
            "source_diff_basis": "N/A",
            "repository_boundaries": [],
            "implementation_quirks": [],
            "avoid_guidance": [],
            "repeat_guidance": [],
            "notes": notes or "N/A",
        }

    return {
        "source_plan": _normalize_scalar(learning.get("source_plan")),
        "source_diff_basis": _normalize_scalar(learning.get("source_diff_basis")),
        "repository_boundaries": _normalize_list(learning.get("repository_boundaries")),
        "implementation_quirks": _normalize_list(learning.get("implementation_quirks")),
        "avoid_guidance": _normalize_list(learning.get("avoid_guidance")),
        "repeat_guidance": _normalize_list(learning.get("repeat_guidance")),
        "notes": _normalize_notes(learning.get("notes")),
    }


def _normalize_scalar(value: object) -> str:
    if value is None:
        return "N/A"
    text = str(value).strip()
    return text or "N/A"


def _normalize_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    return [text] if text else []


def _normalize_notes(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return "\n".join(parts) or "N/A"

    text = str(value).strip()
    return text or "N/A"


def _render_learning_section(payload: dict[str, object]) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = [
        f"## Learnings: {timestamp}",
        "",
        "### Source Plan",
        f"- `{payload['source_plan']}`",
        "",
        "### Source Diff Basis",
        f"- `{payload['source_diff_basis']}`",
        "",
        "### Repository Boundaries",
        _render_list(payload["repository_boundaries"]),
        "",
        "### Repository-Specific Quirks",
        _render_list(payload["implementation_quirks"]),
        "",
        "### Avoid Guidance",
        _render_list(payload["avoid_guidance"]),
        "",
        "### Repeat Guidance",
        _render_list(payload["repeat_guidance"]),
        "",
        "### Notes",
        str(payload["notes"]),
    ]
    return "\n".join(sections).rstrip()


def _render_list(items: object) -> str:
    if not isinstance(items, list) or not items:
        return "- N/A"
    return "\n".join(f"- {item}" for item in items)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
