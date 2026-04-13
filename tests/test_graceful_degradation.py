import json
import importlib.util
import re
import sys
import uuid
from pathlib import Path
import pytest

# Add hooks directory to sys.path for direct imports
sys.path.append(str(Path(".codex/hooks").resolve()))

HOOK_PATH = Path(".codex/hooks/validate_session.py").resolve()
LOCAL_TEMP_ROOT = Path(".tmp-tests").resolve()

def load_hook_module():
    spec = importlib.util.spec_from_file_location("validate_session_hook", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def temp_project(request):
    LOCAL_TEMP_ROOT.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", request.node.name).strip("-") or "temp-project"
    project_dir = LOCAL_TEMP_ROOT / f"{safe_name}-{uuid.uuid4().hex[:8]}"
    project_dir.mkdir(parents=True, exist_ok=False)
    
    # Create .codex directory
    (project_dir / ".codex").mkdir(exist_ok=True)
    
    # Create mix.exs
    (project_dir / "mix.exs").write_text(
        'defmodule MyApp.MixProject do\n'
        '  def project do\n'
        '    [deps: [{:phoenix, "~> 1.7"}, {:phoenix_ecto, "~> 4.4"}, '
        '{:phoenix_live_view, "~> 0.18"}, {:oban, "~> 2.14"}]]\n'
        '  end\n'
        'end'
    )
    
    yield project_dir

def test_validate_session_persists_tidewave_status(temp_project, monkeypatch, capsys):
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))
    monkeypatch.setenv("CODEX_CAPABILITIES", "hooks.v1")
    
    # Mock Tidewave as available
    monkeypatch.setattr(
        module,
        "detect_tidewave_status",
        lambda timeout_seconds=module.TIDEWAVE_TIMEOUT_SECONDS: ("Tidewave MCP: Server command is available (stub).", True),
    )
    
    with pytest.raises(SystemExit):
        module.validate()
        
    env_file = temp_project / ".codex" / "environment.json"
    assert env_file.exists()
    
    data = json.loads(env_file.read_text())
    assert data.get("tidewave_available") is True

def test_validate_session_persists_tidewave_unavailable_status(temp_project, monkeypatch, capsys):
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))
    monkeypatch.setenv("CODEX_CAPABILITIES", "hooks.v1")
    
    # Mock Tidewave as unavailable
    monkeypatch.setattr(
        module,
        "detect_tidewave_status",
        lambda timeout_seconds=module.TIDEWAVE_TIMEOUT_SECONDS: ("Tidewave MCP: Server command is unavailable (stub).", False),
    )
    
    with pytest.raises(SystemExit):
        module.validate()
        
    env_file = temp_project / ".codex" / "environment.json"
    assert env_file.exists()
    
    data = json.loads(env_file.read_text())
    assert data.get("tidewave_available") is False

def test_validate_session_overwrites_non_object_environment_state(temp_project, monkeypatch, capsys):
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))
    monkeypatch.setenv("CODEX_CAPABILITIES", "hooks.v1")

    env_file = temp_project / ".codex" / "environment.json"
    env_file.write_text("[]", encoding="utf-8")

    monkeypatch.setattr(
        module,
        "detect_tidewave_status",
        lambda timeout_seconds=module.TIDEWAVE_TIMEOUT_SECONDS: ("Tidewave MCP: Server command is unavailable (stub).", False),
    )

    with pytest.raises(SystemExit) as exc:
        module.validate()

    assert exc.value.code == 0
    data = json.loads(env_file.read_text())
    assert data == {"tidewave_available": False}

def test_plan_work_injects_tidewave_available(temp_project, monkeypatch):
    import plan_work
    
    # Create a dummy plan
    plan_dir = temp_project / ".codex" / "plans" / "dummy"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "plan.md"
    plan_file.write_text("## Goal\nTest\n## Tasks\n- [ ] Task 1\n")
    
    # Set tidewave as unavailable
    env_file = temp_project / ".codex" / "environment.json"
    env_file.write_text(json.dumps({"tidewave_available": False}))
    
    context = plan_work.get_work_context(plan_file, repo_root=temp_project)
    assert context["tidewave_available"] is False
    
    # Set tidewave as available
    env_file.write_text(json.dumps({"tidewave_available": True}))
    context = plan_work.get_work_context(plan_file, repo_root=temp_project)
    assert context["tidewave_available"] is True


@pytest.mark.parametrize(
    "environment_body",
    [
        "[]",
        json.dumps({"tidewave_available": "false"}),
    ],
)
def test_plan_work_treats_invalid_tidewave_state_as_unknown(temp_project, environment_body):
    import plan_work

    plan_dir = temp_project / ".codex" / "plans" / "dummy"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "plan.md"
    plan_file.write_text("## Goal\nTest\n## Tasks\n- [ ] Task 1\n")

    env_file = temp_project / ".codex" / "environment.json"
    env_file.write_text(environment_body, encoding="utf-8")

    context = plan_work.get_work_context(plan_file, repo_root=temp_project)
    assert context["tidewave_available"] is None

def test_plan_full_coordinate_lifecycle_respects_tidewave_unavailable(temp_project, monkeypatch):
    import plan_full
    import plan_work
    
    # Create a dummy plan
    plan_dir = temp_project / ".codex" / "plans" / "dummy"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "plan.md"
    plan_file.write_text("## Goal\nTest\n## Tasks\n- [ ] Task with tidewave keyword\n")
    
    # Set tidewave as unavailable
    env_file = temp_project / ".codex" / "environment.json"
    env_file.write_text(json.dumps({"tidewave_available": False}))
    
    # We need to ensure coordinate_lifecycle finds our plan
    monkeypatch.setattr(plan_work, "resolve_active_plan", lambda r, t: plan_file)
    
    # Run coordinate_lifecycle with failure count that would normally trigger introspection
    result = plan_full.coordinate_lifecycle(
        repo_root=temp_project,
        consecutive_failures=3
    )
    
    assert result["introspection_recommended"] is False, "Should NOT recommend introspection if tidewave is unavailable"
    
    # Set tidewave as available
    env_file.write_text(json.dumps({"tidewave_available": True}))
    
    result = plan_full.coordinate_lifecycle(
        repo_root=temp_project,
        consecutive_failures=3
    )
    
    assert result["introspection_recommended"] is True, "Should recommend introspection if tidewave is available and threshold reached"

def test_plan_full_keeps_introspection_available_when_tidewave_state_is_unknown(temp_project, monkeypatch):
    import plan_full
    import plan_work

    plan_dir = temp_project / ".codex" / "plans" / "dummy"
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_file = plan_dir / "plan.md"
    plan_file.write_text("## Goal\nTest\n## Tasks\n- [ ] debug LiveView socket timeout\n")

    monkeypatch.setattr(plan_work, "resolve_active_plan", lambda r, t: plan_file)

    result = plan_full.coordinate_lifecycle(
        repo_root=temp_project,
        consecutive_failures=3
    )

    assert result["introspection_recommended"] is True, "Unknown Tidewave state should preserve existing introspection fallback behavior"
