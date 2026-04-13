"""
plan_state.py — Markdown state-machine helper for .codex plan files.

Provides deterministic load/parse/write operations on plan.md files located at
.codex/plans/{slug}/plan.md. The file is the sole source of truth for progress
state; this module intentionally reopens the file on every call so state survives
CLI interruption or session restart with no in-memory continuity required.

Contract:
  - Pending task line  : starts with "- [ ] " (exact, lowercase, ASCII space)
  - Completed task line: starts with "- [x] " (exact, lowercase, ASCII space)
  - Only checklist items inside the "## Tasks" section are actionable tasks
  - Any other bracket variant ([X], [v], [done], etc.) is NOT a recognised task
"""

import os
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

# ---------------------------------------------------------------------------
# Canonical patterns — no flags, no case-folding.
# ---------------------------------------------------------------------------
_PENDING_PREFIX = "- [ ] "
_DONE_PREFIX = "- [x] "
_TASKS_HEADING = "## Tasks"
_SECTION_HEADING_RE = re.compile(r"^#{1,2} ")

# Matches a line that looks like a task but uses an unrecognised marker.
_INVALID_TASK_RE = re.compile(r"^- \[[^\]]\] ")


def _load_lines(plan_path: Path) -> list[str]:
    """Read plan file and return UTF-8 lines with original newline bytes preserved."""
    return plan_path.read_bytes().decode("utf-8").splitlines(keepends=True)


@contextmanager
def _plan_lock(plan_path: Path, timeout: float = 10.0):
    """Simple file-based lock with retry logic and stale lock detection."""
    import json
    import os
    lock_path = plan_path.with_suffix(".lock")
    start_time = time.time()
    pid = os.getpid()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, json.dumps({"pid": pid, "timestamp": start_time}).encode())
            os.close(fd)
            break
        except FileExistsError:
            if time.time() - start_time > timeout:
                try:
                    with open(lock_path) as f:
                        lock_data = json.load(f)
                    if time.time() - lock_data.get("timestamp", 0) > timeout * 2:
                        os.remove(lock_path)
                        continue
                except Exception:
                    pass
                raise TimeoutError(f"Could not acquire lock on {plan_path} after {timeout}s")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError as e:
            raise RuntimeError(f"Failed to remove lock file: {e}")


def _write_lines_atomic(plan_path: Path, lines: list[str]) -> None:
    """Write *lines* to *plan_path* atomically without normalising newlines."""
    payload = "".join(lines).encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(
        dir=plan_path.parent,
        prefix=f".{plan_path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, plan_path)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except PermissionError:
            pass
        raise


def _is_pending(line: str) -> bool:
    return line.startswith(_PENDING_PREFIX)


def _is_done(line: str) -> bool:
    return line.startswith(_DONE_PREFIX)


def _is_invalid_task(line: str) -> bool:
    """Return True if the line looks like a task with an unsupported marker."""
    return bool(_INVALID_TASK_RE.match(line)) and not _is_pending(line) and not _is_done(line)


def _iter_task_section(lines: list[str]):
    """Yield `(index, line)` pairs for content inside the canonical tasks section."""
    in_tasks_section = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == _TASKS_HEADING:
            in_tasks_section = True
            continue
        if in_tasks_section and _SECTION_HEADING_RE.match(stripped):
            break
        if in_tasks_section:
            yield idx, line


def _assert_task_index_in_range(lines: list[str], task_index: int) -> None:
    if task_index < 0 or task_index >= len(lines):
        raise ValueError(f"task_index {task_index} is out of range (file has {len(lines)} lines)")

    task_lines = {idx for idx, _ in _iter_task_section(lines)}
    if task_index not in task_lines:
        raise ValueError(f"Line {task_index} is not inside the ## Tasks section.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_tasks(plan_path: Path) -> list[dict]:
    """Return all recognised task lines from *plan_path*.

    Each item is a dict::

        {"index": int, "text": str, "done": bool}

    where *index* is the zero-based line number inside the file, *text* is the
    task description (no prefix), and *done* is whether the task is completed.

    Lines with invalid checkbox markers are silently ignored (not treated as
    tasks) so the caller never sees them as actionable items.

    Args:
        plan_path: Absolute or relative ``Path`` to the plan.md file.

    Returns:
        List of task dicts in file order.

    Raises:
        FileNotFoundError: If *plan_path* does not exist.
    """
    lines = _load_lines(plan_path)
    tasks: list[dict] = []
    for idx, line in _iter_task_section(lines):
        if _is_pending(line):
            tasks.append({"index": idx, "text": line[len(_PENDING_PREFIX):].rstrip("\n\r"), "done": False})
        elif _is_done(line):
            tasks.append({"index": idx, "text": line[len(_DONE_PREFIX):].rstrip("\n\r"), "done": True})
    return tasks


def find_first_pending(plan_path: Path) -> dict | None:
    """Return the first task with ``done=False``, or *None* if all are done.

    Reopens the file on every call.

    Args:
        plan_path: Path to the plan.md file.

    Returns:
        A task dict ``{"index": int, "text": str, "done": False}`` or *None*.
    """
    for task in load_tasks(plan_path):
        if not task["done"]:
            return task
    return None


def find_most_recent_completed(plan_path: Path) -> dict | None:
    """Return the highest-index completed task, or *None* if none are completed."""
    completed = [task for task in load_tasks(plan_path) if task["done"]]
    if not completed:
        return None
    return max(completed, key=lambda task: task["index"])


def mark_task_complete(plan_path: Path, task_index: int) -> None:
    """Mark the task at line *task_index* as complete in-place with concurrency safety."""
    with _plan_lock(plan_path):
        lines = _load_lines(plan_path)
        _assert_task_index_in_range(lines, task_index)

        line = lines[task_index]
        if not _is_pending(line):
            raise ValueError(
                f"Line {task_index} is not a pending task line. "
                f"Got: {line!r}"
            )
        lines[task_index] = _DONE_PREFIX + line[len(_PENDING_PREFIX):]
        _write_lines_atomic(plan_path, lines)


def reopen_task(plan_path: Path, task_index: int) -> None:
    """Reopen the completed task at line *task_index* with concurrency safety."""
    with _plan_lock(plan_path):
        lines = _load_lines(plan_path)
        _assert_task_index_in_range(lines, task_index)

        line = lines[task_index]
        if not _is_done(line):
            raise ValueError(
                f"Line {task_index} is not a completed task line. "
                f"Got: {line!r}"
            )

        lines[task_index] = _PENDING_PREFIX + line[len(_DONE_PREFIX):]
        _write_lines_atomic(plan_path, lines)


def reopen_most_recent_completed(plan_path: Path) -> dict:
    """Reopen the highest-index completed task and return the reopened task metadata."""
    with _plan_lock(plan_path):
        latest = find_most_recent_completed(plan_path)
        if latest is None:
            raise ValueError("No completed task exists to reopen in the ## Tasks section.")

        reopen_task(plan_path, latest["index"])
        return {
            "index": latest["index"],
            "text": latest["text"],
            "done": False,
        }
