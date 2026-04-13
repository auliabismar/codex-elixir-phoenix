"""
review_enforcement.py -- Semantic Iron Law normalization and rollback helpers.

Normalizes machine-readable iron-law-judge output and applies deterministic
plan rollback semantics when a semantic violation is detected.
"""

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import plan_state
import plan_work

_CANONICAL_LAW_PATH = Path(".codex") / "references" / "iron-laws-canonical.json"


def resolve_plan_binding(repo_root: Path, target: str | Path | None = None) -> dict:
    """Resolve exactly one rollback target plan or return a structured failure."""
    repo_root = Path(repo_root).resolve()
    target_text = _normalize_target(target)

    if target_text:
        return _resolve_explicit_plan_binding(repo_root, target_text)

    return _resolve_auto_plan_binding(repo_root)


def normalize_judge_output(judge_output: str, repo_root: Path | None = None) -> dict:
    """Normalize iron-law-judge XML into a stable Python payload."""
    payload = (judge_output or "").strip()
    if not payload:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": "Judge returned an empty payload.",
            "violation": None,
        }

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": f"Judge returned malformed XML: {exc}",
            "violation": None,
        }

    if root.tag != "iron-law-review":
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": "Judge payload must use <iron-law-review> as the root element.",
            "violation": None,
        }

    child_tags = [child.tag for child in list(root)]
    status = (root.findtext("status") or "").strip().lower()
    if status == "clean":
        if child_tags != ["status"]:
            return {
                "status": "invalid-judge-output",
                "error_type": "invalid-judge-output",
                "message": (
                    "Clean judge payload must contain exactly "
                    "<status>clean</status> and no additional elements."
                ),
                "violation": None,
            }
        return {
            "status": "clean",
            "error_type": None,
            "message": None,
            "violation": None,
        }

    violation_node = root.find("violation")
    if status != "violation" or violation_node is None or child_tags != ["status", "violation"]:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": (
                "Judge payload must contain either "
                "<status>clean</status> or <status>violation</status> with <violation>."
            ),
            "violation": None,
        }

    if sorted(violation_node.attrib) != ["law"]:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": "Judge violation payload must use exactly one 'law' attribute.",
            "violation": None,
        }

    violation_child_tags = [child.tag for child in list(violation_node)]
    if violation_child_tags != ["title", "reasoning", "correction"]:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": (
                "Judge violation payload must contain exactly "
                "<title>, <reasoning>, and <correction> in that order."
            ),
            "violation": None,
        }

    law_number = _extract_law_number(violation_node)
    laws = _load_canonical_laws(repo_root)
    if law_number is None:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": "Judge violation payload must include a canonical law number.",
            "violation": None,
        }

    if law_number not in laws:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": (
                f"Judge reported unknown Iron Law #{law_number}; "
                "violations must map to .codex/references/iron-laws-canonical.json."
            ),
            "violation": None,
        }

    supplied_title = (violation_node.findtext("title") or "").strip()
    reasoning = (violation_node.findtext("reasoning") or "").strip()
    correction = (violation_node.findtext("correction") or "").strip()
    if not supplied_title or not reasoning or not correction:
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": (
                "Judge violation payload must provide non-empty "
                "title, reasoning, and correction text."
            ),
            "violation": None,
        }

    title = laws[law_number].get("title") or supplied_title

    return {
        "status": "violation",
        "error_type": None,
        "message": None,
        "violation": {
            "law_number": law_number,
            "law_title": title,
            "reasoning": reasoning,
            "correction": correction,
        },
    }


def enforce_semantic_gate(
    repo_root: Path,
    judge_output: str,
    target: str | Path | None = None,
    plan_binding: dict | None = None,
) -> dict:
    """Apply semantic verdict and perform deterministic rollback when required."""
    repo_root = Path(repo_root).resolve()
    normalized = normalize_judge_output(judge_output, repo_root=repo_root)
    plan_binding = _resolve_or_reuse_plan_binding(
        repo_root,
        target=target,
        plan_binding=plan_binding,
    )

    if normalized["status"] == "invalid-judge-output":
        return {
            "status": "invalid-judge-output",
            "error_type": "invalid-judge-output",
            "message": normalized["message"],
            "violation": None,
            "rollback": None,
            "plan_binding": plan_binding,
        }

    if normalized["status"] == "clean":
        return {
            "status": "clean",
            "error_type": None,
            "message": "Semantic Iron Law review clean.",
            "violation": None,
            "rollback": None,
            "plan_binding": plan_binding,
        }

    violation = normalized["violation"]

    if plan_binding["status"] != "resolved":
        return {
            "status": plan_binding["status"],
            "error_type": plan_binding["error_type"],
            "message": plan_binding["message"],
            "violation": violation,
            "rollback": None,
            "plan_binding": plan_binding,
        }

    plan_path = Path(str(plan_binding["plan_path"])).resolve()

    try:
        reopened = plan_state.reopen_most_recent_completed(plan_path)
    except ValueError as exc:
        return {
            "status": "no-completed-task",
            "error_type": "no-completed-task",
            "message": str(exc),
            "violation": violation,
            "rollback": None,
            "plan_binding": plan_binding,
        }

    rollback = {
        "plan_path": str(plan_path),
        "plan_slug": plan_binding["plan_slug"],
        "task_index": reopened["index"],
        "task_text": reopened["text"],
    }

    return {
        "status": "violation",
        "error_type": "semantic-violation",
        "message": (
            "Semantic Iron Law violation detected. "
            f"Reopened most recent completed task '{reopened['text']}'."
        ),
        "violation": violation,
        "rollback": rollback,
        "plan_binding": plan_binding,
    }


def prepend_semantic_blocker(enforcement_result: dict, checklist_text: str) -> str:
    """Prepend a dedicated semantic blocker section ahead of the review checklist."""
    checklist = (checklist_text or "").strip()
    violation = enforcement_result.get("violation")

    if not isinstance(violation, dict):
        return checklist

    law_number = violation.get("law_number")
    law_title = str(violation.get("law_title") or "Unspecified Iron Law").strip()
    law_label = law_title if law_number is None else f"#{law_number} {law_title}"

    lines = ["## Semantic Iron Law Blocker"]
    lines.append(f"- Outcome: {enforcement_result.get('status')}")
    lines.append(f"- Violated law: {law_label}")

    reasoning = str(violation.get("reasoning") or "").strip()
    correction = str(violation.get("correction") or "").strip()
    if reasoning:
        lines.append(f"- Reasoning: {reasoning}")
    if correction:
        lines.append(f"- Required correction: {correction}")

    rollback = enforcement_result.get("rollback")
    if isinstance(rollback, dict):
        lines.append(
            "- Plan rollback: reopened "
            f"`{rollback['task_text']}` in `{rollback['plan_path']}` "
            f"(line index {rollback['task_index']})"
        )
    else:
        message = str(enforcement_result.get("message") or "Rollback was not applied.").strip()
        lines.append(f"- Plan rollback: not applied ({message})")

    blocker = "\n".join(lines)
    if not checklist:
        return blocker
    return f"{blocker}\n\n{checklist}"


def _resolve_explicit_plan_binding(repo_root: Path, target: str) -> dict:
    try:
        plan_path = plan_work.resolve_active_plan(repo_root, slug=target)
    except plan_work.AmbiguityError as exc:
        return {
            "status": "ambiguous-target",
            "error_type": "ambiguous-target",
            "message": str(exc),
            "plan_path": None,
            "plan_slug": None,
            "target": target,
        }
    except FileNotFoundError as exc:
        return {
            "status": "no-target",
            "error_type": "no-target",
            "message": str(exc),
            "plan_path": None,
            "plan_slug": None,
            "target": target,
        }

    return {
        "status": "resolved",
        "error_type": None,
        "message": None,
        "plan_path": str(plan_path),
        "plan_slug": plan_path.parent.name,
        "target": target,
    }


def _resolve_auto_plan_binding(repo_root: Path) -> dict:
    plans_dir = repo_root / ".codex" / "plans"
    if not plans_dir.exists():
        return {
            "status": "no-target",
            "error_type": "no-target",
            "message": f"Plans directory missing at {plans_dir}",
            "plan_path": None,
            "plan_slug": None,
            "target": None,
        }

    eligible: list[Path] = []
    for entry in sorted(plans_dir.iterdir(), key=lambda path: path.name):
        if not entry.is_dir() or entry.name == "_template":
            continue

        plan_path = entry / "plan.md"
        if not plan_path.exists():
            continue

        tasks = plan_state.load_tasks(plan_path)
        if any(task["done"] for task in tasks):
            eligible.append(plan_path)

    if not eligible:
        return {
            "status": "no-target",
            "error_type": "no-target",
            "message": (
                "No eligible plan with completed tasks found for semantic rollback. "
                "Provide an explicit plan slug/path: $phx-review <slug>."
            ),
            "plan_path": None,
            "plan_slug": None,
            "target": None,
        }

    if len(eligible) > 1:
        slugs = ", ".join(path.parent.name for path in eligible)
        return {
            "status": "ambiguous-target",
            "error_type": "ambiguous-target",
            "message": (
                f"Multiple eligible plans found: {slugs}. "
                "Provide an explicit plan slug/path for semantic rollback."
            ),
            "plan_path": None,
            "plan_slug": None,
            "target": None,
        }

    plan_path = eligible[0]
    return {
        "status": "resolved",
        "error_type": None,
        "message": None,
        "plan_path": str(plan_path),
        "plan_slug": plan_path.parent.name,
        "target": None,
    }


def _resolve_or_reuse_plan_binding(
    repo_root: Path,
    target: str | Path | None,
    plan_binding: dict | None,
) -> dict:
    if plan_binding is None:
        return resolve_plan_binding(repo_root, target=target)

    if not isinstance(plan_binding, dict):
        return {
            "status": "invalid-plan-binding",
            "error_type": "invalid-plan-binding",
            "message": "Provided plan_binding must be a dict from collect_review_packet().",
            "plan_path": None,
            "plan_slug": None,
            "target": _normalize_target(target),
        }

    required_keys = {"status", "error_type", "message", "plan_path", "plan_slug"}
    missing = sorted(required_keys - set(plan_binding))
    if missing:
        return {
            "status": "invalid-plan-binding",
            "error_type": "invalid-plan-binding",
            "message": (
                "Provided plan_binding is missing required keys: "
                f"{', '.join(missing)}."
            ),
            "plan_path": None,
            "plan_slug": None,
            "target": _normalize_target(target),
        }

    reused = dict(plan_binding)
    reused.setdefault("target", _normalize_target(target))
    return reused


def _load_canonical_laws(repo_root: Path | None) -> dict[int, dict[str, str]]:
    if repo_root is None:
        return {}

    catalog_path = Path(repo_root).resolve() / _CANONICAL_LAW_PATH
    if not catalog_path.exists():
        return {}

    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    laws = data.get("laws")
    if not isinstance(laws, list):
        return {}

    mapped: dict[int, dict[str, str]] = {}
    for item in laws:
        if not isinstance(item, dict):
            continue

        number = item.get("number")
        if not isinstance(number, int):
            continue

        mapped[number] = {
            "title": str(item.get("title") or "").strip(),
            "wording": str(item.get("wording") or "").strip(),
        }

    return mapped


def _extract_law_number(node: ET.Element) -> int | None:
    law = node.attrib.get("law")
    if law is not None:
        match = re.search(r"\d+", str(law))
        if match:
            return int(match.group(0))
    return None


def _normalize_target(target: str | Path | None) -> str | None:
    if target is None:
        return None
    text = str(target).strip()
    return text or None
