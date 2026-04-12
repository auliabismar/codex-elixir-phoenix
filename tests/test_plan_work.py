"""
tests/test_plan_work.py

Tests for the plan_work orchestration helper (.codex/hooks/plan_work.py).

Covers:
  - Active plan resolution (single plan found)
  - _template exclusion
  - Multiple plans ambiguity handling (raises exception)
  - Explicit slug/path resolution and path-safety guards
  - Work context extraction (goal, tasks, notes)
  - Single-task completion and sequential resume behaviour
"""

import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# Allow importing from the shipped .codex/hooks directory.
HOOKS_DIR = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from plan_work import (  # type: ignore # noqa: E402
    AmbiguityError,
    complete_current_task,
    get_work_context,
    resolve_active_plan,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def repo_root(tmp_path):
    """Return a temporary directory structured like a Codex repo."""
    root = tmp_path / "repo"
    root.mkdir()
    plans_dir = root / ".codex" / "plans"
    plans_dir.mkdir(parents=True)
    
    # Create the template directory (should be excluded)
    template_dir = plans_dir / "_template"
    template_dir.mkdir()
    (template_dir / "plan.md").write_text("# Template\n## Tasks\n- [ ] do nothing", encoding="utf-8")
    
    return root


@pytest.fixture
def plan_factory(repo_root):
    """Return a factory that creates plans in the mock repo."""
    def _make(slug: str, content: str) -> Path:
        plan_dir = repo_root / ".codex" / "plans" / slug
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plan_dir / "plan.md"
        plan_path.write_text(textwrap.dedent(content), encoding="utf-8")
        return plan_path
    return _make


# ---------------------------------------------------------------------------
# resolve_active_plan tests
# ---------------------------------------------------------------------------

class TestResolveActivePlan:
    def test_finds_single_incomplete_plan(self, repo_root, plan_factory):
        plan_factory("feature-one", "# Feature One\n## Tasks\n- [ ] task 1")

        path = resolve_active_plan(repo_root)
        assert path.name == "plan.md"
        assert "feature-one" in str(path)

    def test_excludes_template_directory(self, repo_root):
        # Only _template exists
        with pytest.raises(FileNotFoundError, match="No active plans found"):
            resolve_active_plan(repo_root)

    def test_excludes_fully_completed_plans(self, repo_root, plan_factory):
        plan_factory("done-feature", "# Done\n## Tasks\n- [x] already finished")

        with pytest.raises(FileNotFoundError, match="No active plans found"):
            resolve_active_plan(repo_root)

    def test_raises_ambiguity_error_for_multiple_incomplete_plans(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [ ] task 1")
        plan_factory("feature-two", "## Tasks\n- [ ] task 2")

        with pytest.raises(AmbiguityError, match="Multiple incomplete plans found"):
            resolve_active_plan(repo_root)

    def test_resolves_explicit_slug(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [ ] task 1")
        plan_factory("feature-two", "## Tasks\n- [ ] task 2")

        path = resolve_active_plan(repo_root, slug="feature-two")
        assert "feature-two" in str(path)

    def test_resolves_explicit_repo_relative_plan_path(self, repo_root, plan_factory):
        plan_path = plan_factory("feature-two", "## Tasks\n- [ ] task 2")

        path = resolve_active_plan(repo_root, slug=".codex/plans/feature-two/plan.md")
        assert path == plan_path

    def test_raises_file_not_found_for_invalid_slug(self, repo_root):
        with pytest.raises(FileNotFoundError, match="Plan 'missing' not found"):
            resolve_active_plan(repo_root, slug="missing")

    def test_explicit_completed_plan_still_resolves(self, repo_root, plan_factory):
        plan_path = plan_factory("done-feature", "## Tasks\n- [x] already finished")

        path = resolve_active_plan(repo_root, slug="done-feature")
        assert path == plan_path

    def test_rejects_explicit_template_target(self, repo_root):
        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_active_plan(repo_root, slug=".codex/plans/_template/plan.md")

    def test_rejects_out_of_scope_explicit_target(self, repo_root):
        outside_dir = repo_root / ".codex" / "outside"
        outside_dir.mkdir(parents=True)
        (outside_dir / "plan.md").write_text("## Tasks\n- [ ] surprise", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_active_plan(repo_root, slug="../outside")


# ---------------------------------------------------------------------------
# get_work_context tests
# ---------------------------------------------------------------------------

class TestGetWorkContext:
    def test_extracts_full_context(self, repo_root, plan_factory):
        content = """\
        # Feature: Auth
        
        ## Goal
        
        Implement secure login.
        
        ## Tasks
        
        - [x] setup db
        - [ ] add login form
        - [ ] bcrypt hash
        
        ## Notes

        Use Argon2 if possible.
        """
        p = plan_factory("auth", content)

        ctx = get_work_context(p)
        assert ctx["goal"] == "Implement secure login."
        assert ctx["task"] == "add login form"
        assert ctx["notes"] == "Use Argon2 if possible."
        assert ctx["plan_path"] == str(p)
        assert len(ctx["completed_tasks"]) == 1
        assert ctx["completed_tasks"][0] == "setup db"
        assert ctx["complete"] is False

    def test_handles_missing_sections_gracefully(self, repo_root, plan_factory):
        p = plan_factory("minimal", "## Tasks\n- [ ] just this")
        ctx = get_work_context(p)
        assert ctx["task"] == "just this"
        assert ctx["goal"] == "N/A"
        assert ctx["notes"] == "N/A"
        assert ctx["complete"] is False

    def test_reports_completed_plan_without_error(self, repo_root, plan_factory):
        p = plan_factory("done", "## Tasks\n- [x] wrapped up")

        ctx = get_work_context(p)
        assert ctx["task"] is None
        assert ctx["task_index"] is None
        assert ctx["completed_tasks"] == ["wrapped up"]
        assert ctx["complete"] is True

    def test_includes_reference_context_when_repo_root_is_provided(self, repo_root, plan_factory):
        references_dir = repo_root / ".codex" / "references"
        (references_dir / "ecto").mkdir(parents=True, exist_ok=True)
        (references_dir / "testing").mkdir(parents=True, exist_ok=True)
        (references_dir / "routing.json").write_text(
            textwrap.dedent(
                """\
                {
                  "routes": [
                    {
                      "keywords": ["schema"],
                      "domain": "ecto",
                      "references": ["ecto-schema-basics.md"]
                    },
                    {
                      "keywords": ["test"],
                      "domain": "testing",
                      "references": ["testing-basics.md"]
                    }
                  ],
                  "fallback": {
                    "references": ["elixir-basics.md", "code-organization.md"]
                  }
                }
                """
            ),
            encoding="utf-8",
        )
        (references_dir / "ecto" / "ecto-schema-basics.md").write_text(
            "# Ecto Schema Basics",
            encoding="utf-8",
        )
        (references_dir / "testing" / "testing-basics.md").write_text(
            "# Testing Basics",
            encoding="utf-8",
        )
        (references_dir / "elixir-basics.md").write_text("# Elixir Basics", encoding="utf-8")
        (references_dir / "code-organization.md").write_text(
            "# Code Organization",
            encoding="utf-8",
        )
        plan_path = plan_factory("auth", "## Tasks\n- [ ] add schema test")

        ctx = get_work_context(plan_path, repo_root=repo_root, max_refs=3)

        assert [ref["domain"] for ref in ctx["references"]] == ["ecto", "testing"]
        assert "<reference" in ctx["reference_block"]
        assert "<![CDATA[" in ctx["reference_block"]

    def test_ignores_heading_like_content_inside_fenced_blocks(self, repo_root, plan_factory):
        content = """\
        ## Goal

        Implement secure login.

        ```md
        ## Notes
        not the real notes
        ```

        ## Tasks

        - [ ] add login form

        ## Notes

        Use Argon2 if possible.
        """
        p = plan_factory("fenced", content)

        ctx = get_work_context(p)
        assert "Implement secure login." in ctx["goal"]
        assert "## Notes" in ctx["goal"]
        assert ctx["notes"] == "Use Argon2 if possible."


# ---------------------------------------------------------------------------
# complete_current_task tests
# ---------------------------------------------------------------------------

class TestCompleteCurrentTask:
    @patch("plan_work.validate_compilation.validate_project")
    def test_marks_only_first_pending_task_and_advances_cycle(self, mock_validate, repo_root, plan_factory):
        mock_validate.return_value = {"success": True, "error_type": None, "logs": None}
        content = """\
        ## Goal

        Ship the next chunk.

        ## Tasks

        - [ ] task 1
        - [ ] task 2

        ## Notes

        N/A
        """
        p = plan_factory("cycle", content)

        ctx1 = get_work_context(p)
        result = complete_current_task(p, task_index=ctx1["task_index"])
        ctx2 = get_work_context(p)

        assert result["completed"] is True
        assert result["task"] == "task 1"
        assert result["complete"] is False
        assert result["next_task"] == "task 2"
        assert ctx2["task"] == "task 2"
        assert ctx2["completed_tasks"] == ["task 1"]
        assert "- [x] task 1" in p.read_text(encoding="utf-8")
        assert "- [ ] task 2" in p.read_text(encoding="utf-8")

    @patch("plan_work.validate_compilation.validate_project")
    def test_finds_repo_root_for_nested_plan_paths(self, mock_validate, repo_root):
        mock_validate.return_value = {"success": True, "error_type": None, "logs": None}
        plan_dir = repo_root / ".codex" / "plans" / "nested" / "child"
        plan_dir.mkdir(parents=True)
        plan_path = plan_dir / "plan.md"
        plan_path.write_text("## Tasks\n- [ ] nested task", encoding="utf-8")

        result = complete_current_task(plan_path)

        assert result["completed"] is True
        mock_validate.assert_called_once_with(repo_root)

    @patch("plan_work.validate_compilation.validate_project")
    def test_uses_plan_state_write_semantics_for_completion(self, mock_validate, repo_root):
        mock_validate.return_value = {"success": True, "error_type": None, "logs": None}
        plan_dir = repo_root / ".codex" / "plans" / "line-endings"
        plan_dir.mkdir(parents=True)
        plan_path = plan_dir / "plan.md"
        before = (
            b"# Feature\r\n\r\n"
            b"## Goal\r\n\r\n"
            b"Keep line endings.\r\n\r\n"
            b"## Tasks\r\n\r\n"
            b"- [ ] task 1\r\n"
            b"- [ ] task 2\r\n\r\n"
            b"## Notes\r\n\r\n"
            b"N/A\r\n"
        )
        plan_path.write_bytes(before)

        result = complete_current_task(plan_path)
        after = plan_path.read_bytes()

        assert result["completed"] is True
        assert after == before.replace(b"- [ ] task 1", b"- [x] task 1", 1)

    def test_noops_when_plan_is_already_complete(self, repo_root, plan_factory):
        # No need to mock validate_compilation here because it shouldn't be called if plan is complete
        p = plan_factory("done", "## Tasks\n- [x] wrapped up")
        before = p.read_bytes()

        result = complete_current_task(p)

        assert result["completed"] is False
        assert result["complete"] is True
        assert p.read_bytes() == before

    @patch("plan_work.validate_compilation.validate_project")
    def test_blocks_completion_on_verification_failure(self, mock_validate, repo_root, plan_factory):
        mock_validate.return_value = {
            "success": False,
            "error_type": "compilation",
            "logs": "Syntax error at line 42",
        }
        p = plan_factory("fail-check", "## Tasks\n- [ ] buggy task")

        result = complete_current_task(p)

        assert result["completed"] is False
        assert result["error_type"] == "compilation"
        assert "Syntax error" in result["logs"]
        # Check that the file was NOT modified
        assert "- [ ] buggy task" in p.read_text(encoding="utf-8")
