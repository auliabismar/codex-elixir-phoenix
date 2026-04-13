"""
tests/test_review_packet.py

Tests for the $phx-review packet helper (.codex/hooks/review_packet.py).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from review_packet import collect_review_packet  # noqa: E402


@pytest.fixture
def repo_root(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    return root


@patch("review_packet.validate_compilation.validate_project")
def test_returns_verification_payload_when_verify_fails(mock_validate, repo_root):
    mock_validate.return_value = {
        "success": False,
        "error_type": "compilation",
        "logs": "Compilation failed",
    }

    packet = collect_review_packet(repo_root)

    assert packet["ready"] is False
    assert packet["error_type"] == "verification"
    assert packet["verification"]["success"] is False
    assert packet["verification"]["error_type"] == "compilation"
    assert packet["git_diff"] is None


@patch("review_packet.plan_compound._collect_git_diff")
@patch("review_packet.validate_compilation.validate_project")
def test_returns_packet_after_passing_verify(mock_validate, mock_collect_diff, repo_root):
    mock_validate.return_value = {
        "success": True,
        "error_type": None,
        "logs": None,
    }
    mock_collect_diff.return_value = "diff --git a/lib/app.ex b/lib/app.ex"

    packet = collect_review_packet(repo_root)

    assert packet["ready"] is True
    assert packet["repo_root"] == str(repo_root)
    assert packet["git_diff"] == "diff --git a/lib/app.ex b/lib/app.ex"
    assert packet["source_diff_basis"] == "git diff HEAD plus added untracked source files"
    assert packet["verification"]["success"] is True


@patch("review_packet.plan_compound._collect_git_diff")
@patch("review_packet.validate_compilation.validate_project")
def test_fails_closed_when_git_is_unavailable(mock_validate, mock_collect_diff, repo_root):
    mock_validate.return_value = {
        "success": True,
        "error_type": None,
        "logs": None,
    }
    mock_collect_diff.side_effect = ValueError("Git is required to compound learnings in this repository.")

    packet = collect_review_packet(repo_root)

    assert packet["ready"] is False
    assert packet["error_type"] == "git"
    assert "Git is required" in packet["message"]


@patch("review_packet.plan_compound._collect_git_diff")
@patch("review_packet.validate_compilation.validate_project")
def test_fails_closed_when_diff_is_empty(mock_validate, mock_collect_diff, repo_root):
    mock_validate.return_value = {
        "success": True,
        "error_type": None,
        "logs": None,
    }
    mock_collect_diff.side_effect = ValueError(
        "No meaningful diff found to analyze. Ensure your implementation changes exist in the working tree."
    )

    packet = collect_review_packet(repo_root)

    assert packet["ready"] is False
    assert packet["error_type"] == "empty-diff"
    assert "No meaningful diff" in packet["message"]
