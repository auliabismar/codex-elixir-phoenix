"""
plan_work.py — Orchestration helper for resolving active plans and task context.

Encapsulates the logic for deterministic plan selection and context extraction
for the implementer agent.
"""

import json
from pathlib import Path
import plan_state
import reference_router
import validate_compilation


def get_tidewave_availability(repo_root: Path) -> bool | None:
    """Return Tidewave availability, or None when the state is unknown."""
    env_file = repo_root / ".codex" / "environment.json"
    if not env_file.exists():
        return None

    try:
        data = json.loads(env_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return None

        value = data.get("tidewave_available")
        if isinstance(value, bool):
            return value
    except (json.JSONDecodeError, OSError):
        return None

    return None



class AmbiguityError(Exception):
    """Raised when multiple incomplete plans exist and no target was specified."""

    pass


def resolve_active_plan(repo_root: Path, slug: str = None) -> Path:
    """Find the target plan.md in .codex/plans/.

    Rules:
      1. If `slug` is provided, resolve it as a slug or explicit plan path.
      2. If no slug, scan .codex/plans/ for subdirectories (excluding _template).
      3. Filter for plans that have at least one pending task.
      4. If exactly one exists, return it.
      5. If multiple exist, raise AmbiguityError.
      6. If none exist, raise FileNotFoundError.
    """
    repo_root = repo_root.resolve()
    plans_dir = repo_root / ".codex" / "plans"

    if slug:
        return _resolve_explicit_plan(repo_root, plans_dir, slug)

    if not plans_dir.exists():
        raise FileNotFoundError(f"Plans directory missing at {plans_dir}")

    incomplete_plans = []
    for entry in sorted(plans_dir.iterdir(), key=lambda path: path.name):
        if not entry.is_dir() or entry.name == "_template":
            continue

        plan_path = entry / "plan.md"
        if not plan_path.exists():
            continue

        if plan_state.find_first_pending(plan_path) is not None:
            incomplete_plans.append(plan_path)

    if not incomplete_plans:
        raise FileNotFoundError("No active plans found in .codex/plans/")

    if len(incomplete_plans) > 1:
        slugs = sorted([p.parent.name for p in incomplete_plans])
        raise AmbiguityError(
            f"Multiple incomplete plans found: {', '.join(slugs)}. "
            "Please specify which one to work on: $phx-work <slug>"
        )

    return incomplete_plans[0]


def get_work_context(
    plan_path: Path,
    repo_root: Path | None = None,
    max_refs: int = 3,
) -> dict:
    """Extract implementation context from a plan file.

    Returns a dictionary for the implementer agent.
    """
    content = plan_path.read_text(encoding="utf-8")

    goal = _extract_section(content, "Goal")
    notes = _extract_section(content, "Notes")

    tasks = plan_state.load_tasks(plan_path)
    pending = [t for t in tasks if not t["done"]]
    done = [t for t in tasks if t["done"]]

    tidewave_available = None
    if repo_root is not None:
        tidewave_available = get_tidewave_availability(repo_root)

    if not pending:
        return {
            "plan_path": str(plan_path),
            "goal": goal,
            "notes": notes,
            "task": None,
            "task_index": None,
            "completed_tasks": [t["text"] for t in done],
            "references": [],
            "reference_block": "",
            "tidewave_available": tidewave_available,
            "complete": True,
        }

    reference_context = {"references": [], "reference_block": ""}
    if repo_root is not None:
        reference_context = reference_router.build_reference_context(
            repo_root,
            pending[0]["text"],
            max_refs=max_refs,
        )

    return {
        "plan_path": str(plan_path),
        "goal": goal,
        "notes": notes,
        "task": pending[0]["text"],
        "task_index": pending[0]["index"],
        "completed_tasks": [t["text"] for t in done],
        **reference_context,
        "tidewave_available": tidewave_available,
        "complete": False,
    }


def complete_current_task(
    plan_path: Path,
    task_index: int | None = None,
    repo_root: Path | None = None,
) -> dict:
    """Mark the first pending task complete, or report that the plan is already complete.

    Includes an incremental verification loop via $phx-verify logic.
    """
    pending = plan_state.find_first_pending(plan_path)
    if pending is None:
        return {
            "plan_path": str(plan_path),
            "completed": False,
            "task": None,
            "task_index": None,
            "next_task": None,
            "next_task_index": None,
            "complete": True,
        }

    if task_index is not None and pending["index"] != task_index:
        raise ValueError(
            f"Expected first pending task at line {task_index}, "
            f"found {pending['index']}."
        )

    # Verification Loop
    if repo_root is None:
        repo_root = _find_repo_root(plan_path)
    else:
        repo_root = Path(repo_root).resolve()

    verification = validate_compilation.validate_project(repo_root)
    if not verification["success"]:
        return {
            "plan_path": str(plan_path),
            "completed": False,
            "explanation": f"Verification failed: {verification['error_type']}",
            "error_type": verification["error_type"],
            "logs": verification["logs"],
            "task": pending["text"],
            "task_index": pending["index"],
            "complete": False,
        }

    plan_state.mark_task_complete(plan_path, pending["index"])
    next_pending = plan_state.find_first_pending(plan_path)

    return {
        "plan_path": str(plan_path),
        "completed": True,
        "verification": "success",
        "task": pending["text"],
        "task_index": pending["index"],
        "next_task": next_pending["text"] if next_pending else None,
        "next_task_index": next_pending["index"] if next_pending else None,
        "complete": next_pending is None,
    }


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


def _find_repo_root(start_path: Path) -> Path:
    probe = Path(start_path).resolve()
    search_root = probe.parent if probe.is_file() else probe

    if probe.is_file() and probe.name == "plan.md":
        for parent in [search_root] + list(search_root.parents):
            plans_root = parent / ".codex" / "plans"
            if _is_relative_to(probe, plans_root):
                return parent

    for parent in [search_root] + list(search_root.parents):
        if (parent / ".git").exists():
            return parent

    raise FileNotFoundError(f"Git repository not found for {start_path}")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _extract_section(content: str, name: str) -> str:
    target_heading = f"## {name}"
    in_fence = False
    collecting = False
    collected: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if collecting:
                collected.append(line)
            in_fence = not in_fence
            continue

        if not in_fence and stripped == target_heading:
            collecting = True
            collected = []
            continue

        if not in_fence and collecting and stripped.startswith("## "):
            break

        if collecting:
            collected.append(line)

    text = "\n".join(collected).strip()
    return text or "N/A"
