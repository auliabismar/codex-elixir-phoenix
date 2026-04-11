"""
tests/test_plan_builder.py

Tests for the plan builder helper (.codex/hooks/plan_builder.py).
"""

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
TEMPLATE_SOURCE = REPO_ROOT / ".codex" / "plans" / "_template" / "plan.md"
sys.path.insert(0, str(HOOKS_DIR))

from plan_builder import create_plan_file, normalize_slug  # noqa: E402
from plan_state import find_first_pending, load_tasks  # noqa: E402


@pytest.fixture
def scratch_root() -> Path:
    root = Path.cwd() / ".tmp-tests"
    root.mkdir(exist_ok=True)
    return root


@pytest.fixture
def repo_root(scratch_root: Path) -> Path:
    root = scratch_root / f"plan-builder-{uuid.uuid4().hex}"
    template_dir = root / ".codex" / "plans" / "_template"
    template_dir.mkdir(parents=True)
    template_dir.joinpath("plan.md").write_text(TEMPLATE_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    return root


def test_normalize_slug_strips_only_leading_boilerplate() -> None:
    assert normalize_slug("Create a state of the art dashboard") == "state-of-the-art-dashboard"
    assert normalize_slug("Generate an invoice PDF summary") == "invoice-pdf-summary"


@pytest.mark.parametrize("text", ["Create a", "!!!", "生成计划"])
def test_normalize_slug_rejects_empty_slug(text: str) -> None:
    with pytest.raises(ValueError, match="non-empty plan slug"):
        normalize_slug(text)


def test_normalize_slug_rejects_windows_reserved_name() -> None:
    with pytest.raises(ValueError, match="reserved on Windows"):
        normalize_slug("Create CON")


def test_create_plan_file_writes_template_and_round_trips(repo_root: Path) -> None:
    plan_path = create_plan_file(
        repo_root=repo_root,
        slug=normalize_slug("Create an invoice PDF generator"),
        goal="Generate invoice PDFs from billing records.",
        tasks=[
            "Inspect the billing schema and required PDF fields",
            "Implement the PDF generation pipeline",
            "Add verification coverage for generated plans",
        ],
        notes="Validate parser compatibility before shipping.",
    )

    assert plan_path == repo_root / ".codex" / "plans" / "invoice-pdf-generator" / "plan.md"
    content = plan_path.read_text(encoding="utf-8")
    assert "# Plan: invoice-pdf-generator" in content
    assert "## Goal" in content
    assert "## Tasks" in content
    assert "## Notes" in content
    assert "{slug}" not in content
    assert "- [ ] Inspect the billing schema and required PDF fields" in content

    tasks = load_tasks(plan_path)
    assert [task["text"] for task in tasks] == [
        "Inspect the billing schema and required PDF fields",
        "Implement the PDF generation pipeline",
        "Add verification coverage for generated plans",
    ]
    assert find_first_pending(plan_path)["text"] == "Inspect the billing schema and required PDF fields"


def test_create_plan_file_rejects_empty_tasks(repo_root: Path) -> None:
    with pytest.raises(ValueError, match="tasks must include at least one non-empty item"):
        create_plan_file(
            repo_root=repo_root,
            slug="invoice-pdf-generator",
            goal="Generate invoice PDFs from billing records.",
            tasks=[],
        )


def test_create_plan_file_does_not_overwrite_existing_plan(repo_root: Path) -> None:
    first_path = create_plan_file(
        repo_root=repo_root,
        slug="invoice-pdf-generator",
        goal="Generate invoice PDFs from billing records.",
        tasks=["Inspect the billing schema"],
    )

    with pytest.raises(FileExistsError):
        create_plan_file(
            repo_root=repo_root,
            slug="invoice-pdf-generator",
            goal="Overwriting should fail.",
            tasks=["Different task"],
        )

    assert "Inspect the billing schema" in first_path.read_text(encoding="utf-8")


def test_create_plan_file_rejects_reserved_slug(repo_root: Path) -> None:
    with pytest.raises(ValueError, match="reserved on Windows"):
        create_plan_file(
            repo_root=repo_root,
            slug="con",
            goal="Should fail on Windows reserved names.",
            tasks=["Inspect the billing schema"],
        )


def test_create_plan_file_rejects_non_kebab_case_slug(repo_root: Path) -> None:
    with pytest.raises(ValueError, match="must be kebab-case ASCII"):
        create_plan_file(
            repo_root=repo_root,
            slug="Invoice PDF Generator",
            goal="Should fail for invalid slug shapes.",
            tasks=["Inspect the billing schema"],
        )
