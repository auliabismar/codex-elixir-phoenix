"""
plan_full.py — Orchestration helper for the fully autonomous lifecycle.

Composes planning, work, verification, review, and compounding into a 
unified coordinator with a bounded recovery loop.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure sibling hooks can be imported when run as a standalone script.
sys.path.append(str(Path(__file__).parent))

import plan_builder  # type: ignore
import plan_aggregator  # type: ignore
import plan_work  # type: ignore
import review_packet  # type: ignore
import review_aggregator  # type: ignore
import review_enforcement  # type: ignore
import plan_compound  # type: ignore


def coordinate_lifecycle(
    repo_root: Path,
    target: Optional[str] = None,
    consecutive_failures: int = 0,
) -> Dict[str, Any]:
    """
    Coordinate the $phx-full autonomous lifecycle.
    
    Returns a structured payload indicating the current stage and next action.
    """
    repo_root = Path(repo_root).resolve()
    
    # 1. Resolve or Create Plan
    try:
        plan_path = plan_work.resolve_active_plan(repo_root, target)
    except (FileNotFoundError, plan_work.AmbiguityError):
        # If no plan exists or target is freeform text, we might need to plan first.
        # This is handled by the orchestrator agent deciding to call phx-plan.
        return {
            "stage": "planning",
            "status": "pending",
            "message": "No active plan resolved. Decision required: Create new plan or specify target.",
            "target": target
        }

    plan_slug = plan_path.parent.name
    
    # 2. Check Plan Status
    work_context = plan_work.get_work_context(plan_path, repo_root=repo_root)
    
    if not work_context["complete"]:
        # We are in the WORK loop
        if consecutive_failures > 3:
            return {
                "stage": "work",
                "status": "halted",
                "plan_slug": plan_slug,
                "plan_path": str(plan_path),
                "consecutive_failures": consecutive_failures,
                "message": "Halted: Recovery budget exhausted (> 3 consecutive verification failures).",
                "task": work_context["task"],
                "task_index": work_context["task_index"]
            }
            
        return {
            "stage": "work",
            "status": "in-progress",
            "plan_slug": plan_slug,
            "plan_path": str(plan_path),
            "consecutive_failures": consecutive_failures,
            "task": work_context["task"],
            "task_index": work_context["task_index"],
            "task_id": f"{plan_slug}:{work_context['task_index']}",
            "reference_block": work_context["reference_block"]
        }

    # 3. Plan implementation is complete, proceed to REVIEW
    packet = review_packet.collect_review_packet(repo_root, target=plan_path)
    
    if not packet["ready"]:
        # Verification must pass before review
        if packet.get("error_type") == "verification":
            # This shouldn't happen if phx-work/verify is working correctly, 
            # but we handle it as a recovery failure.
            return {
                "stage": "work",
                "status": "in-progress",
                "plan_slug": plan_slug,
                "plan_path": str(plan_path),
                "consecutive_failures": consecutive_failures + 1,
                "message": "Review prerequisite failed: verification regression.",
                "error_type": "verification"
            }
        
        return {
            "stage": "review",
            "status": "fail-closed",
            "plan_slug": plan_slug,
            "message": packet["message"],
            "error_type": packet.get("error_type")
        }

    # 4. Review is ready
    # The actual fan-out and aggregation is handled by the orchestrator agent 
    # using parallel-reviewer and iron-law-judge.
    # We return the packet to allow the agent to proceed.
    return {
        "stage": "review",
        "status": "ready",
        "plan_slug": plan_slug,
        "plan_path": str(plan_path),
        "packet": packet
    }


def finalize_lifecycle(
    repo_root: Path,
    plan_path: Path,
    review_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle the end of the review phase: rollback, rework, or compound.
    """
    repo_root = Path(repo_root).resolve()
    plan_path = Path(plan_path).resolve()
    
    # Enforce semantic gate
    rollback = review_enforcement.enforce_semantic_gate(
        repo_root, 
        review_results.get("judge_output", ""),
        target=plan_path
    )
    
    if rollback["status"] == "violation":
        return {
            "stage": "work",
            "status": "rollback",
            "plan_slug": plan_path.parent.name,
            "message": rollback["message"],
            "reopened_task": rollback.get("reopened_task")
        }

    # Check for advisory findings
    # (Assuming review_results includes aggregated checklist)
    advisory_findings = review_results.get("advisory_findings", [])
    if advisory_findings:
        return {
            "stage": "work",
            "status": "rework",
            "plan_slug": plan_path.parent.name,
            "message": "Advisory findings detected. Proceeding to rework.",
            "findings": advisory_findings
        }

    # 5. Clean review, proceed to COMPOUND
    try:
        analysis_packet = plan_compound.get_analysis_packet(plan_path)
        return {
            "stage": "compound",
            "status": "ready",
            "plan_slug": plan_path.parent.name,
            "analysis_packet": analysis_packet
        }
    except Exception as exc:
        return {
            "stage": "compound",
            "status": "error",
            "message": str(exc)
        }
