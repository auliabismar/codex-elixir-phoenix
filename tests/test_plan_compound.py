"""
tests/test_plan_compound.py
"""

import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Allow importing from the shipped .codex/hooks directory.
HOOKS_DIR = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from plan_compound import (  # noqa: E402
    AmbiguityError,
    _collect_git_diff,
    get_analysis_packet,
    persist_learning,
    resolve_target_plan,
)


@pytest.fixture
def repo_root(tmp_path):
    """Return a temporary directory structured like a Codex repo."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".codex" / "plans").mkdir(parents=True)
    return root


@pytest.fixture
def plan_factory(repo_root):
    """Return a factory that creates plans in the mock repo."""

    def _make(slug: str, content: str) -> Path:
        plan_dir = repo_root / ".codex" / "plans" / slug
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plan_dir / "plan.md"
        plan_path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")
        return plan_path

    return _make


class TestResolveTargetPlan:
    def test_finds_single_completed_plan(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [x] task 1")
        plan_factory("feature-two", "## Tasks\n- [ ] task 2")

        path = resolve_target_plan(repo_root)
        assert path.name == "plan.md"
        assert "feature-one" in str(path)

    def test_ignores_plans_without_recognized_tasks(self, repo_root, plan_factory):
        plan_factory("notes-only", "# Notes only")
        plan_factory("feature-one", "## Tasks\n- [x] task 1")

        path = resolve_target_plan(repo_root)
        assert "feature-one" in str(path)

    def test_raises_file_not_found_when_no_completed_plans(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [ ] task 1")
        plan_factory("notes-only", "# Notes only")

        with pytest.raises(FileNotFoundError, match="No completed plans found"):
            resolve_target_plan(repo_root)

    def test_raises_ambiguity_error_for_multiple_completed_plans(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [x] task 1")
        plan_factory("feature-two", "## Tasks\n- [x] task 2")

        with pytest.raises(AmbiguityError, match="Multiple completed plans found"):
            resolve_target_plan(repo_root)

    def test_rejects_explicit_targets_outside_codex_plans(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [x] task 1")
        outside = repo_root / "notes.md"
        outside.write_text("# not a plan\n", encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="not found"):
            resolve_target_plan(repo_root, target=str(outside))

    def test_rejects_explicit_incomplete_plan(self, repo_root, plan_factory):
        plan_factory("feature-one", "## Tasks\n- [ ] task 1")

        with pytest.raises(ValueError, match="is not complete"):
            resolve_target_plan(repo_root, target="feature-one")


class TestGetAnalysisPacket:
    def test_gathers_structured_packet(self, repo_root, plan_factory, monkeypatch):
        plan_path = plan_factory(
            "auth",
            """
            ## Goal
            Build login

            ## Notes
            Keep it simple

            ## Tasks
            - [x] create login page
            - [x] persist session
            """,
        )

        monkeypatch.setattr(
            "plan_compound._collect_git_diff",
            lambda _: "diff --git a/app.py b/app.py",
        )

        packet = get_analysis_packet(plan_path)

        assert packet["slug"] == "auth"
        assert packet["goal"] == "Build login"
        assert packet["notes"] == "Keep it simple"
        assert packet["completed_tasks"] == ["create login page", "persist session"]
        assert packet["complete"] is True
        assert packet["git_diff"] == "diff --git a/app.py b/app.py"
        assert packet["source_diff_basis"] == "git diff HEAD plus added untracked source files"
        assert packet["repo_root"] == str(repo_root)

    def test_requires_completed_plan(self, repo_root, plan_factory):
        plan_path = plan_factory("auth", "## Tasks\n- [ ] create login page")

        with pytest.raises(ValueError, match="is not complete"):
            get_analysis_packet(plan_path)


class TestCollectGitDiff:
    @patch("plan_compound.subprocess.run")
    def test_includes_untracked_and_ignored_source_files(self, mock_run, repo_root):
        def run_side_effect(args, cwd, capture_output, text, check=False):
            assert cwd == str(repo_root)
            if args[:3] == ["git", "diff", "HEAD"]:
                return MagicMock(returncode=0, stdout="", stderr="")
            if args[:5] == ["git", "status", "--porcelain=v1", "-z", "--ignored=matching"]:
                return MagicMock(
                    returncode=0,
                    stdout="?? .codex/hooks/new_hook.py\0!! tests/test_new_hook.py\0!! .pytest_cache/v/cache.py\0",
                    stderr="",
                )
            if args[-1] == ".codex/hooks/new_hook.py":
                return MagicMock(returncode=1, stdout="diff for hook", stderr="")
            if args[-1] == "tests/test_new_hook.py":
                return MagicMock(returncode=1, stdout="diff for test", stderr="")
            raise AssertionError(f"Unexpected git command: {args}")

        mock_run.side_effect = run_side_effect

        diff = _collect_git_diff(repo_root)

        assert "diff for hook" in diff
        assert "diff for test" in diff
        assert ".pytest_cache" not in diff

    @patch("plan_compound.subprocess.run")
    def test_raises_on_git_failures(self, mock_run, repo_root):
        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="fatal: bad revision 'HEAD'")

        with pytest.raises(ValueError, match="Git diff HEAD failed"):
            _collect_git_diff(repo_root)


class TestPersistLearning:
    def test_creates_new_memory_file_with_schema(self, repo_root):
        path = persist_learning(
            repo_root,
            "user-auth",
            {
                "source_plan": ".codex/plans/user-auth/plan.md",
                "source_diff_basis": "git diff HEAD plus added untracked source files",
                "repository_boundaries": ["Authentication lives in Accounts."],
                "implementation_quirks": ["Reuse the existing session plug."],
                "avoid_guidance": ["Do not write auth logic in controllers."],
                "repeat_guidance": ["Keep login flows inside the Accounts context."],
                "notes": "Validated with targeted pytest coverage.",
            },
        )

        assert path.exists()
        text = path.read_text(encoding="utf-8")
        assert "# Agent Memory: user-auth" in text
        assert "### Source Plan" in text
        assert "`git diff HEAD plus added untracked source files`" in text
        assert "### Repository Boundaries" in text
        assert "### Repository-Specific Quirks" in text
        assert "### Avoid Guidance" in text
        assert "### Repeat Guidance" in text
        assert "### Notes" in text

    def test_appends_to_existing_memory_file(self, repo_root):
        first = persist_learning(repo_root, "user-auth", "Old note")
        persist_learning(repo_root, "user-auth", "New note.")

        text = first.read_text(encoding="utf-8")
        assert "Old note" in text
        assert "New note." in text
        assert text.count("## Learnings:") == 2

    def test_rejects_unsafe_slugs(self, repo_root):
        with pytest.raises(ValueError, match="path separators"):
            persist_learning(repo_root, "../user-auth", "nope")
