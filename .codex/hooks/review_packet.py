"""
review_packet.py -- Deterministic packet builder for $phx-review.

Runs the same verification gate used by $phx-verify and, only on success,
collects the current source diff packet for parallel semantic review.
"""

from pathlib import Path

import plan_compound
import validate_compilation


def collect_review_packet(repo_root: Path) -> dict:
    """Return a fail-closed review packet for the current workspace diff."""
    repo_root = Path(repo_root).resolve()
    verification = validate_compilation.validate_project(repo_root)
    base_packet = {
        "repo_root": str(repo_root),
        "git_diff": None,
        "source_diff_basis": plan_compound._SOURCE_DIFF_BASIS,
        "verification": verification,
    }

    if not verification["success"]:
        return {
            **base_packet,
            "ready": False,
            "error_type": "verification",
            "message": (
                "Verification prerequisite failed. "
                "Run $phx-verify and address reported errors before $phx-review."
            ),
        }

    try:
        git_diff = plan_compound._collect_git_diff(repo_root)
    except ValueError as exc:
        message = str(exc).strip() or "Unable to gather review diff."
        return {
            **base_packet,
            "ready": False,
            "error_type": _classify_diff_failure(message),
            "message": message,
        }

    return {
        **base_packet,
        "ready": True,
        "git_diff": git_diff,
        "error_type": None,
        "message": None,
    }


def _classify_diff_failure(message: str) -> str:
    normalized = message.lower()
    if "no meaningful diff" in normalized:
        return "empty-diff"
    if "git" in normalized or "repository" in normalized:
        return "git"
    return "diff"
