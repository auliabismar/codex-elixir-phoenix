"""
tests/test_review_enforcement.py

Tests for semantic Iron Law enforcement and plan rollback helpers.
"""

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from review_enforcement import (  # noqa: E402
    enforce_semantic_gate,
    prepend_semantic_blocker,
)

CLEAN_XML = "<iron-law-review><status>clean</status></iron-law-review>"
VIOLATION_XML = """
<iron-law-review>
  <status>violation</status>
  <violation law="7">
    <title>Oban jobs must be idempotent</title>
    <reasoning>Side-effecting worker can enqueue duplicates on retries.</reasoning>
    <correction>Add unique: [keys: [...], period: ...] to use Oban.Worker.</correction>
  </violation>
</iron-law-review>
"""


@pytest.fixture
def repo_root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".codex" / "plans").mkdir(parents=True)
    refs_dir = root / ".codex" / "references"
    refs_dir.mkdir(parents=True)
    catalog = {
        "snapshot_date": "2026-04-13",
        "provenance": "upstream README + judge contract",
        "laws": [
            {
                "number": 7,
                "title": "Oban jobs must be idempotent",
                "wording": "Jobs MUST be idempotent.",
            }
        ],
    }
    (refs_dir / "iron-laws-canonical.json").write_text(
        json.dumps(catalog, indent=2),
        encoding="utf-8",
    )
    return root


def _write_plan(repo_root: Path, slug: str, body: str) -> Path:
    plan_dir = repo_root / ".codex" / "plans" / slug
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plan_dir / "plan.md"
    plan_path.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return plan_path


def test_returns_clean_status_without_rollback_when_judge_is_clean(repo_root):
    result = enforce_semantic_gate(repo_root, CLEAN_XML)

    assert result["status"] == "clean"
    assert result["rollback"] is None
    assert result["violation"] is None


def test_rejects_clean_payload_with_extra_violation_node(repo_root):
    plan_path = _write_plan(repo_root, "payments", "## Tasks\n- [x] done")
    before = plan_path.read_text(encoding="utf-8")
    malformed_clean = """
    <iron-law-review>
      <status>clean</status>
      <violation law="7">
        <title>Oban jobs must be idempotent</title>
        <reasoning>contradictory</reasoning>
        <correction>remove violation node</correction>
      </violation>
    </iron-law-review>
    """

    result = enforce_semantic_gate(repo_root, malformed_clean, target="payments")

    assert result["status"] == "invalid-judge-output"
    assert result["rollback"] is None
    assert plan_path.read_text(encoding="utf-8") == before


def test_rolls_back_last_completed_task_when_violation_detected(repo_root):
    plan_path = _write_plan(
        repo_root,
        "payments",
        """
        ## Tasks

        - [x] add worker module
        - [x] enqueue payment refresh
        - [ ] wire dashboard refresh
        """,
    )

    result = enforce_semantic_gate(repo_root, VIOLATION_XML, target="payments")

    assert result["status"] == "violation"
    assert result["violation"]["law_number"] == 7
    assert result["violation"]["law_title"] == "Oban jobs must be idempotent"
    assert result["rollback"]["task_text"] == "enqueue payment refresh"
    assert "- [x] add worker module\n" in plan_path.read_text(encoding="utf-8")
    assert "- [ ] enqueue payment refresh\n" in plan_path.read_text(encoding="utf-8")


def test_rejects_unknown_law_numbers_without_rollback(repo_root):
    plan_path = _write_plan(repo_root, "payments", "## Tasks\n- [x] done")
    before = plan_path.read_text(encoding="utf-8")
    unknown_law_xml = """
    <iron-law-review>
      <status>violation</status>
      <violation law="999">
        <title>Imaginary law</title>
        <reasoning>not in the catalog</reasoning>
        <correction>pick a real law</correction>
      </violation>
    </iron-law-review>
    """

    result = enforce_semantic_gate(repo_root, unknown_law_xml, target="payments")

    assert result["status"] == "invalid-judge-output"
    assert result["rollback"] is None
    assert plan_path.read_text(encoding="utf-8") == before


def test_rejects_violation_payload_with_unexpected_child_nodes(repo_root):
    plan_path = _write_plan(repo_root, "payments", "## Tasks\n- [x] done")
    before = plan_path.read_text(encoding="utf-8")
    malformed_violation = """
    <iron-law-review>
      <status>violation</status>
      <violation law="7">
        <title>Oban jobs must be idempotent</title>
        <reasoning>side effects are duplicated</reasoning>
        <correction>add unique keys</correction>
        <junk>unexpected</junk>
      </violation>
    </iron-law-review>
    """

    result = enforce_semantic_gate(repo_root, malformed_violation, target="payments")

    assert result["status"] == "invalid-judge-output"
    assert result["rollback"] is None
    assert plan_path.read_text(encoding="utf-8") == before


def test_uses_supplied_plan_binding_without_re_resolving_target(repo_root):
    plan_a = _write_plan(repo_root, "payments", "## Tasks\n- [x] add worker\n- [ ] verify worker\n")
    plan_b = _write_plan(repo_root, "orders", "## Tasks\n- [x] unrelated done\n")
    provided_binding = {
        "status": "resolved",
        "error_type": None,
        "message": None,
        "plan_path": str(plan_a),
        "plan_slug": "payments",
        "target": "payments",
    }
    before_b = plan_b.read_text(encoding="utf-8")

    with patch("review_enforcement.resolve_plan_binding") as mock_resolve:
        result = enforce_semantic_gate(
            repo_root,
            VIOLATION_XML,
            target="orders",
            plan_binding=provided_binding,
        )

    mock_resolve.assert_not_called()
    assert result["status"] == "violation"
    assert "- [ ] add worker\n" in plan_a.read_text(encoding="utf-8")
    assert plan_b.read_text(encoding="utf-8") == before_b


def test_fails_closed_with_ambiguous_target_when_multiple_plans_are_eligible(repo_root):
    plan_one = _write_plan(repo_root, "feature-a", "## Tasks\n- [x] done")
    plan_two = _write_plan(repo_root, "feature-b", "## Tasks\n- [x] done")
    before_one = plan_one.read_text(encoding="utf-8")
    before_two = plan_two.read_text(encoding="utf-8")

    result = enforce_semantic_gate(repo_root, VIOLATION_XML)

    assert result["status"] == "ambiguous-target"
    assert result["rollback"] is None
    assert plan_one.read_text(encoding="utf-8") == before_one
    assert plan_two.read_text(encoding="utf-8") == before_two


def test_fails_closed_when_explicit_target_has_no_completed_tasks(repo_root):
    plan_path = _write_plan(repo_root, "feature-a", "## Tasks\n- [ ] pending only")
    before = plan_path.read_text(encoding="utf-8")

    result = enforce_semantic_gate(repo_root, VIOLATION_XML, target="feature-a")

    assert result["status"] == "no-completed-task"
    assert result["rollback"] is None
    assert plan_path.read_text(encoding="utf-8") == before


def test_fails_closed_with_no_target_when_no_plan_can_be_resolved(repo_root):
    result = enforce_semantic_gate(repo_root, VIOLATION_XML)

    assert result["status"] == "no-target"
    assert result["rollback"] is None


def test_prepends_semantic_blocker_before_review_checklist(repo_root):
    _write_plan(repo_root, "payments", "## Tasks\n- [x] done")
    result = enforce_semantic_gate(repo_root, VIOLATION_XML, target="payments")
    checklist = "Prioritized Refactoring Checklist\n1. [MEDIUM] tighten naming"

    rendered = prepend_semantic_blocker(result, checklist)

    assert rendered.startswith("## Semantic Iron Law Blocker")
    assert "Prioritized Refactoring Checklist" in rendered
