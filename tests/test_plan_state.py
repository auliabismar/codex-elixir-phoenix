"""
tests/test_plan_state.py

Tests for the plan_state markdown state-machine helper (.codex/hooks/plan_state.py).

Covers:
  - Exact checkbox matching ([ ] pending, [x] done)
  - Only the canonical ## Tasks section is parsed
  - First-pending-task selection
  - Invalid marker rejection ([X], [v], [done], and similar)
  - Round-trip write: only the targeted task changes; surrounding markdown preserved
  - Repeated open/update cycles against the same file
"""

import sys
import textwrap
import uuid
from pathlib import Path

import pytest

# Allow importing from the shipped .codex/hooks directory without installing.
HOOKS_DIR = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

import plan_state  # noqa: E402
from plan_state import load_tasks, find_first_pending, mark_task_complete  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scratch_root():
    root = Path.cwd() / ".tmp-tests"
    root.mkdir(exist_ok=True)
    return root


@pytest.fixture
def simulated_replace(monkeypatch):
    def _replace(src, dst):
        Path(dst).write_bytes(Path(src).read_bytes())

    monkeypatch.setattr(plan_state.os, "replace", _replace)


@pytest.fixture
def plan_file(scratch_root):
    """Return a factory that writes a repo-local temp plan.md and returns its Path."""
    created: list[Path] = []

    def _make(content: str) -> Path:
        p = scratch_root / f"plan-{uuid.uuid4().hex}.md"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        created.append(p)
        return p

    yield _make

    for path in created:
        try:
            path.unlink(missing_ok=True)
        except PermissionError:
            pass


# ---------------------------------------------------------------------------
# load_tasks — basic recognition
# ---------------------------------------------------------------------------

class TestLoadTasks:
    def test_recognises_pending_task(self, plan_file):
        p = plan_file("""\
            # Plan

            ## Tasks

            - [ ] do something
        """)
        tasks = load_tasks(p)
        assert len(tasks) == 1
        assert tasks[0]["done"] is False
        assert tasks[0]["text"] == "do something"

    def test_recognises_done_task(self, plan_file):
        p = plan_file("""\
            # Plan

            ## Tasks

            - [x] already done
        """)
        tasks = load_tasks(p)
        assert len(tasks) == 1
        assert tasks[0]["done"] is True
        assert tasks[0]["text"] == "already done"

    def test_mixed_pending_and_done(self, plan_file):
        p = plan_file("""\
            ## Tasks

            - [x] first done
            - [ ] second pending
            - [x] third done
            - [ ] fourth pending
        """)
        tasks = load_tasks(p)
        assert len(tasks) == 4
        assert [t["done"] for t in tasks] == [True, False, True, False]

    def test_returns_correct_line_indices(self, plan_file):
        content = "# Title\n\n## Tasks\n\n- [ ] task one\n- [x] task two\n"
        p = plan_file(content)
        tasks = load_tasks(p)
        # Line 4 (0-based) => "- [ ] task one"
        assert tasks[0]["index"] == 4
        # Line 5 => "- [x] task two"
        assert tasks[1]["index"] == 5

    def test_empty_file_returns_empty_list(self, plan_file):
        p = plan_file("")
        assert load_tasks(p) == []

    def test_file_with_no_tasks_returns_empty_list(self, plan_file):
        p = plan_file("""\
            # Plan: my-feature

            ## Goal

            Do stuff.

            ## Notes

            Some notes here.
        """)
        assert load_tasks(p) == []

    def test_ignores_checklists_outside_tasks_section(self, plan_file):
        p = plan_file("""\
            # Plan

            ## Goal

            - [ ] not a task

            ## Tasks

            - [ ] actual task

            ## Notes

            - [x] also not a task
        """)
        tasks = load_tasks(p)
        assert len(tasks) == 1
        assert tasks[0]["text"] == "actual task"

    def test_raises_file_not_found(self, scratch_root):
        with pytest.raises(FileNotFoundError):
            load_tasks(scratch_root / f"missing-{uuid.uuid4().hex}.md")


# ---------------------------------------------------------------------------
# load_tasks — invalid marker rejection
# ---------------------------------------------------------------------------

class TestInvalidMarkers:
    """Invalid variants must NOT be returned as tasks."""

    @pytest.mark.parametrize("bad_line", [
        "- [X] uppercase X\n",
        "- [V] uppercase V\n",
        "- [v] lowercase v\n",
        "- [done] word marker\n",
        "- [✓] unicode check\n",
        "- [ x] space before x\n",
        "- [x ] space after x\n",
        "- [] empty brackets\n",
        "- [  ] double space\n",
    ])
    def test_invalid_marker_not_recognised(self, plan_file, bad_line):
        p = plan_file(f"# Plan\n\n## Tasks\n\n{bad_line}")
        tasks = load_tasks(p)
        assert tasks == [], f"Expected no tasks for line {bad_line!r}, got {tasks}"

    def test_valid_tasks_survive_alongside_invalid_lines(self, plan_file):
        p = plan_file("""\
            ## Tasks

            - [X] invalid uppercase
            - [ ] valid pending
            - [done] invalid word
            - [x] valid done
        """)
        tasks = load_tasks(p)
        assert len(tasks) == 2
        assert tasks[0]["done"] is False
        assert tasks[1]["done"] is True


# ---------------------------------------------------------------------------
# find_first_pending
# ---------------------------------------------------------------------------

class TestFindFirstPending:
    def test_returns_first_pending_task(self, plan_file):
        p = plan_file("""\
            ## Tasks

            - [x] done first
            - [ ] pending second
            - [ ] pending third
        """)
        task = find_first_pending(p)
        assert task is not None
        assert task["text"] == "pending second"
        assert task["done"] is False

    def test_returns_none_when_all_done(self, plan_file):
        p = plan_file("""\
            ## Tasks

            - [x] done one
            - [x] done two
        """)
        assert find_first_pending(p) is None

    def test_returns_none_for_empty_file(self, plan_file):
        p = plan_file("")
        assert find_first_pending(p) is None

    def test_returns_none_for_no_tasks(self, plan_file):
        p = plan_file("# Just a heading\n\nSome prose.\n")
        assert find_first_pending(p) is None

    def test_reopens_file_fresh_after_external_write(self, plan_file):
        """find_first_pending must reflect the current file state, not cached state."""
        p = plan_file("## Tasks\n\n- [ ] step one\n- [ ] step two\n")
        first = find_first_pending(p)
        assert first["text"] == "step one"

        # Externally mark the first task done (simulating another process).
        p.write_text("## Tasks\n\n- [x] step one\n- [ ] step two\n", encoding="utf-8")

        second = find_first_pending(p)
        assert second is not None
        assert second["text"] == "step two"


# ---------------------------------------------------------------------------
# mark_task_complete — round-trip write behaviour
# ---------------------------------------------------------------------------

class TestMarkTaskComplete:
    def test_marks_pending_task_done(self, plan_file, simulated_replace):
        p = plan_file("## Tasks\n\n- [ ] do the thing\n")
        tasks = load_tasks(p)
        mark_task_complete(p, tasks[0]["index"])
        updated = load_tasks(p)
        assert len(updated) == 1
        assert updated[0]["done"] is True

    def test_only_targeted_task_changes(self, plan_file, simulated_replace):
        content = (
            "# Plan\n"
            "\n"
            "## Tasks\n"
            "\n"
            "- [ ] task one\n"
            "- [ ] task two\n"
            "- [ ] task three\n"
            "\n"
            "## Notes\n"
            "\n"
            "Keep this section intact.\n"
        )
        p = plan_file(content)
        tasks = load_tasks(p)
        # Mark the middle task (task two) complete.
        target = next(t for t in tasks if t["text"] == "task two")
        mark_task_complete(p, target["index"])

        result = p.read_text(encoding="utf-8")
        assert "- [x] task two\n" in result
        assert "- [ ] task one\n" in result
        assert "- [ ] task three\n" in result
        # Non-task markdown must be untouched.
        assert "## Notes\n" in result
        assert "Keep this section intact.\n" in result

    def test_surrounding_markdown_preserved_exactly(self, plan_file, simulated_replace):
        content = (
            "# Plan: my-slug\n"
            "\n"
            "## Goal\n"
            "\n"
            "Accomplish the mission.\n"
            "\n"
            "## Tasks\n"
            "\n"
            "- [ ] first task\n"
            "- [ ] second task\n"
            "\n"
            "## Notes\n"
            "\n"
            "Some notes.\n"
        )
        p = plan_file(content)
        tasks = load_tasks(p)
        mark_task_complete(p, tasks[0]["index"])

        after = p.read_text(encoding="utf-8")
        expected = content.replace("- [ ] first task\n", "- [x] first task\n")
        assert after == expected

    def test_preserves_crlf_newlines_exactly(self, scratch_root, simulated_replace):
        p = scratch_root / f"plan-{uuid.uuid4().hex}.md"
        original = (
            b"# Plan\r\n"
            b"\r\n"
            b"## Tasks\r\n"
            b"\r\n"
            b"- [ ] first task\r\n"
            b"- [ ] second task\r\n"
            b"\r\n"
            b"## Notes\r\n"
            b"\r\n"
            b"Reference only.\r\n"
        )
        p.write_bytes(original)
        task_index = load_tasks(p)[0]["index"]

        mark_task_complete(p, task_index)

        expected = original.replace(b"- [ ] first task\r\n", b"- [x] first task\r\n", 1)
        assert p.read_bytes() == expected
        try:
            p.unlink(missing_ok=True)
        except PermissionError:
            pass

    def test_uses_atomic_replace_so_original_survives_write_failure(self, plan_file, monkeypatch):
        p = plan_file("""\
            ## Tasks

            - [ ] first task
            - [ ] second task
        """)
        original = p.read_bytes()
        task_index = load_tasks(p)[0]["index"]

        def fail_replace(src, dst):
            raise OSError("replace failed")

        monkeypatch.setattr(plan_state.os, "replace", fail_replace)

        with pytest.raises(OSError, match="replace failed"):
            mark_task_complete(p, task_index)

        assert p.read_bytes() == original

    def test_raises_for_already_done_task(self, plan_file, simulated_replace):
        p = plan_file("## Tasks\n\n- [x] already done\n")
        tasks = load_tasks(p)
        with pytest.raises(ValueError, match="not a pending task"):
            mark_task_complete(p, tasks[0]["index"])

    def test_raises_for_out_of_range_index(self, plan_file, simulated_replace):
        p = plan_file("## Tasks\n\n- [ ] only task\n")
        with pytest.raises(ValueError, match="out of range"):
            mark_task_complete(p, 999)

    def test_raises_for_negative_index(self, plan_file, simulated_replace):
        p = plan_file("## Tasks\n\n- [ ] only task\n")
        with pytest.raises(ValueError, match="out of range"):
            mark_task_complete(p, -1)

    def test_raises_for_non_task_line(self, plan_file):
        p = plan_file("# A heading\n## Tasks\n- [ ] real task\n")
        with pytest.raises(ValueError, match="not inside the ## Tasks section"):
            mark_task_complete(p, 0)  # line 0 is a heading, not a task

    def test_raises_for_pending_line_outside_tasks_section(self, plan_file, simulated_replace):
        p = plan_file("""\
            ## Tasks

            - [ ] actual task

            ## Notes

            - [ ] example only
        """)
        with pytest.raises(ValueError, match="not inside the ## Tasks section"):
            mark_task_complete(p, 6)

    def test_raises_file_not_found(self, scratch_root):
        with pytest.raises(FileNotFoundError):
            mark_task_complete(scratch_root / f"missing-{uuid.uuid4().hex}.md", 0)


# ---------------------------------------------------------------------------
# Repeated open/update cycles — resilience
# ---------------------------------------------------------------------------

class TestRepeatedCycles:
    def test_sequential_completions_converge_correctly(self, plan_file, simulated_replace):
        """Completing tasks one by one should leave the file fully checked."""
        p = plan_file("""\
            ## Tasks

            - [ ] alpha
            - [ ] beta
            - [ ] gamma
        """)
        for _ in range(3):
            task = find_first_pending(p)
            assert task is not None
            mark_task_complete(p, task["index"])

        # All tasks should now be done.
        assert find_first_pending(p) is None
        tasks = load_tasks(p)
        assert all(t["done"] for t in tasks)

    def test_state_survives_simulated_restart(self, plan_file, simulated_replace):
        """Verify that re-importing the module path still reads current state."""
        p = plan_file("## Tasks\n\n- [ ] step one\n- [ ] step two\n- [ ] step three\n")

        # Session 1: complete step one.
        t = find_first_pending(p)
        mark_task_complete(p, t["index"])

        # Simulate restart — re-read from scratch (no in-memory carry-over).
        tasks_after_restart = load_tasks(p)
        pending = [t for t in tasks_after_restart if not t["done"]]
        assert len(pending) == 2
        assert pending[0]["text"] == "step two"
