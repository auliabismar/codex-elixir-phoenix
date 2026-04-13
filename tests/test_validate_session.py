import importlib.util
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = Path(".codex/hooks/validate_session.py").resolve()
LOCAL_TEMP_ROOT = Path(".tmp-tests").resolve()


def load_hook_module():
    spec = importlib.util.spec_from_file_location("validate_session_hook", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_mix_exs(target):
    (target / "mix.exs").write_text(
        'defmodule MyApp.MixProject do\n'
        '  def project do\n'
        '    [deps: [{:phoenix, "~> 1.7"}, {:phoenix_ecto, "~> 4.4"}, '
        '{:phoenix_live_view, "~> 0.18"}, {:oban, "~> 2.14"}]]\n'
        '  end\n'
        'end'
    )


def run_validate(module, capsys):
    with pytest.raises(SystemExit) as exc:
        module.validate()
    return exc.value.code, capsys.readouterr()


@pytest.fixture
def temp_project(request):
    LOCAL_TEMP_ROOT.mkdir(exist_ok=True)
    project_dir = LOCAL_TEMP_ROOT / request.node.name
    project_dir.mkdir(exist_ok=True)

    mix_exs = project_dir / "mix.exs"
    if mix_exs.exists():
        mix_exs.unlink()

    yield project_dir


def test_fails_without_mix_exs(temp_project, monkeypatch, capsys):
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))

    exit_code, captured = run_validate(module, capsys)

    assert exit_code == 1
    assert "mix.exs not found" in captured.err.lower()


def test_fails_with_missing_dependencies(temp_project, monkeypatch, capsys):
    (temp_project / "mix.exs").write_text('defmodule MyApp.MixProject do\n  def project do\n    [deps: []]\n  end\nend')
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))

    exit_code, captured = run_validate(module, capsys)

    assert exit_code == 1
    assert "missing phoenix dependencies" in captured.err.lower()


def test_passes_with_phoenix_dependencies(temp_project, monkeypatch, capsys):
    write_mix_exs(temp_project)
    monkeypatch.setenv("CODEX_CAPABILITIES", "hooks.v1")
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))
    monkeypatch.setattr(
        module,
        "detect_tidewave_status",
        lambda timeout_seconds=module.TIDEWAVE_TIMEOUT_SECONDS: ("Tidewave MCP: Server command is available (stub).", True),
    )

    exit_code, captured = run_validate(module, capsys)

    assert exit_code == 0
    assert "environment validation successful." in captured.out.lower()


def test_fails_without_codex_capabilities(temp_project, monkeypatch, capsys):
    write_mix_exs(temp_project)
    monkeypatch.delenv("CODEX_CAPABILITIES", raising=False)
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))

    exit_code, captured = run_validate(module, capsys)

    assert exit_code == 1
    assert "codex cli capability" in captured.err.lower()


def test_logs_tidewave_status(temp_project, monkeypatch, capsys):
    write_mix_exs(temp_project)
    monkeypatch.setenv("CODEX_CAPABILITIES", "hooks.v1")
    module = load_hook_module()
    monkeypatch.setattr(module.Path, "cwd", classmethod(lambda cls: temp_project))
    monkeypatch.setattr(
        module,
        "detect_tidewave_status",
        lambda timeout_seconds=module.TIDEWAVE_TIMEOUT_SECONDS: ("Tidewave MCP: Server command is available (stub).", True),
    )

    exit_code, captured = run_validate(module, capsys)

    assert exit_code == 0
    assert "Tidewave MCP: Server command is available (stub)." in captured.out


def test_detect_tidewave_status_probes_configured_server(monkeypatch):
    module = load_hook_module()
    calls = []

    monkeypatch.setattr(module, "load_tidewave_command", lambda: ["npx", "-y", "@tidewave/mcp-server"])

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    message, available = module.detect_tidewave_status()
    
    assert message == "Tidewave MCP: Server command is available (npx -y @tidewave/mcp-server)."
    assert available is True
    assert calls == [
        (
            ["npx", "-y", "@tidewave/mcp-server", "--help"],
            {
                "capture_output": True,
                "text": True,
                "check": False,
                "timeout": module.TIDEWAVE_TIMEOUT_SECONDS,
            },
        )
    ]


def test_detect_tidewave_status_times_out(monkeypatch):
    module = load_hook_module()
    monkeypatch.setattr(module, "load_tidewave_command", lambda: ["npx", "-y", "@tidewave/mcp-server"])

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    message, available = module.detect_tidewave_status()
    
    assert "timed out" in message
    assert available is False
    assert "Introspection will be limited." in message
