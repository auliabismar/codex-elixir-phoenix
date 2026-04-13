import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

# Story 7.1: Eval Harness Infrastructure

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
LOCAL_TEMP_ROOT = REPO_ROOT / ".tmp-evals"

if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def _build_child_env(
    extra_env: dict[str, str] | None = None,
    path_prepend: Path | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_entries = [str(HOOKS_DIR)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)

    if path_prepend is not None:
        existing_path = env.get("PATH")
        prepend = str(path_prepend)
        env["PATH"] = os.pathsep.join([prepend, existing_path]) if existing_path else prepend

    if extra_env:
        env.update(extra_env)

    return env


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def hook_path():
    """Path to the iron law gateway hook."""
    return HOOKS_DIR / "iron_law_gateway.py"


@pytest.fixture
def payload_runner(hook_path, repo_root):
    """
    Runner that pipes a JSON payload to the Iron Law Gateway hook.
    Returns (exit_code, stdout, stderr).
    """
    def _run(
        payload: dict,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ):
        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            cwd=str(cwd or repo_root),
            env=_build_child_env(env),
        )
        return process.returncode, process.stdout, process.stderr

    return _run


@pytest.fixture
def python_runner(repo_root):
    """Run Python snippets in a separate process with hook imports available."""

    def _run(
        script: str,
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        path_prepend: Path | None = None,
    ):
        return subprocess.run(
            [sys.executable, "-c", script],
            text=True,
            capture_output=True,
            cwd=str(cwd or repo_root),
            env=_build_child_env(env, path_prepend=path_prepend),
        )

    return _run


@pytest.fixture
def temp_project(request):
    LOCAL_TEMP_ROOT.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", request.node.name).strip("-") or "eval"
    project_dir = LOCAL_TEMP_ROOT / f"{safe_name}-{uuid.uuid4().hex[:8]}"
    project_dir.mkdir(
        parents=True,
        exist_ok=False,
    )
    (project_dir / ".codex").mkdir(exist_ok=True)
    yield project_dir
    shutil.rmtree(project_dir, ignore_errors=True)
