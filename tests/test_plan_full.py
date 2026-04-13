"""
tests/test_plan_full.py

Deterministic pytest coverage for full-cycle orchestration and stop conditions.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Allow importing from the shipped .codex/hooks directory.
HOOKS_DIR = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from plan_full import coordinate_lifecycle, finalize_lifecycle  # type: ignore # noqa: E402


@pytest.fixture
def repo_root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    plans_dir = root / ".codex" / "plans"
    plans_dir.mkdir(parents=True)
    return root


@pytest.fixture
def plan_path(repo_root):
    plan_dir = repo_root / ".codex" / "plans" / "test-feature"
    plan_dir.mkdir(parents=True)
    path = plan_dir / "plan.md"
    path.write_text("## Tasks\n- [ ] task 1", encoding="utf-8")
    return path


class TestCoordinateLifecycle:
    
    @patch("plan_work.resolve_active_plan")
    def test_returns_planning_stage_on_resolve_failure(self, mock_resolve, repo_root):
        mock_resolve.side_effect = FileNotFoundError("No active plans found")
        
        result = coordinate_lifecycle(repo_root, target="new-feature")
        
        assert result["stage"] == "planning"
        assert result["status"] == "pending"
        assert result["target"] == "new-feature"

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    def test_returns_work_stage_when_incomplete(self, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {
            "complete": False,
            "task": "task 1",
            "task_index": 1,
            "reference_block": "some refs"
        }
        
        result = coordinate_lifecycle(repo_root)
        
        assert result["stage"] == "work"
        assert result["status"] == "in-progress"
        assert result["plan_slug"] == "test-feature"
        assert result["task"] == "task 1"
        assert result["task_id"] == "test-feature:1"

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    def test_recommends_introspection_for_stateful_tasks_after_threshold(self, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {
            "complete": False,
            "task": "debug LiveView socket timeout",
            "task_index": 1,
            "reference_block": ""
        }

        result = coordinate_lifecycle(repo_root, consecutive_failures=2)

        assert result["introspection_recommended"] is True
        assert result["consecutive_failures"] == 2

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    def test_does_not_recommend_introspection_for_generic_failures(self, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {
            "complete": False,
            "task": "task 1",
            "task_index": 1,
            "reference_block": ""
        }

        result = coordinate_lifecycle(repo_root, consecutive_failures=2)

        assert result["introspection_recommended"] is False

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    def test_recommends_introspection_for_failure_context_keywords(self, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {
            "complete": False,
            "task": "task 1",
            "task_index": 1,
            "reference_block": ""
        }

        result = coordinate_lifecycle(
            repo_root,
            consecutive_failures=2,
            failure_context="GenServer timeout in handle_call during retry",
        )

        assert result["introspection_recommended"] is True

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    def test_halts_when_recovery_budget_exhausted(self, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {
            "complete": False,
            "task": "task 1",
            "task_index": 1,
            "reference_block": ""
        }
        
        result = coordinate_lifecycle(repo_root, consecutive_failures=4)
        
        assert result["stage"] == "work"
        assert result["status"] == "halted"
        assert "Recovery budget exhausted" in result["message"]

    @patch("plan_work.resolve_active_plan")
    @patch("plan_work.get_work_context")
    @patch("review_packet.collect_review_packet")
    def test_returns_review_ready_when_work_complete(self, mock_collect, mock_get_context, mock_resolve, repo_root, plan_path):
        mock_resolve.return_value = plan_path
        mock_get_context.return_value = {"complete": True}
        mock_collect.return_value = {"ready": True, "git_diff": "some diff"}
        
        result = coordinate_lifecycle(repo_root)
        
        assert result["stage"] == "review"
        assert result["status"] == "ready"
        assert result["plan_slug"] == "test-feature"


class TestFinalizeLifecycle:
    
    @patch("review_enforcement.enforce_semantic_gate")
    def test_returns_rollback_on_violation(self, mock_gate, repo_root, plan_path):
        mock_gate.return_value = {
            "status": "violation",
            "message": "Iron Law broken",
            "reopened_task": "task 1"
        }
        
        result = finalize_lifecycle(repo_root, plan_path, {"judge_output": "bad"})
        
        assert result["stage"] == "work"
        assert result["status"] == "rollback"
        assert result["reopened_task"] == "task 1"

    @patch("review_enforcement.enforce_semantic_gate")
    def test_returns_rework_on_advisory_findings(self, mock_gate, repo_root, plan_path):
        mock_gate.return_value = {"status": "clean"}
        review_results = {
            "judge_output": "good",
            "advisory_findings": ["Fix typo"]
        }
        
        result = finalize_lifecycle(repo_root, plan_path, review_results)
        
        assert result["stage"] == "work"
        assert result["status"] == "rework"
        assert result["findings"] == ["Fix typo"]

    @patch("review_enforcement.enforce_semantic_gate")
    @patch("plan_compound.get_analysis_packet")
    def test_returns_compound_ready_on_clean_review(self, mock_packet, mock_gate, repo_root, plan_path):
        mock_gate.return_value = {"status": "clean"}
        mock_packet.return_value = {"slug": "test-feature", "complete": True}
        
        result = finalize_lifecycle(repo_root, plan_path, {"judge_output": "good"})
        
        assert result["stage"] == "compound"
        assert result["status"] == "ready"
        assert result["plan_slug"] == "test-feature"
