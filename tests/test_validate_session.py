import os
import sys
import subprocess
import pytest
import tempfile
from pathlib import Path

HOOK_PATH = os.path.abspath(".codex/hooks/validate_session.py")

@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(old_cwd)

def run_hook(env=None):
    if env is None:
        env = os.environ.copy()
    
    # We use sys.executable to run the script in same python environment
    result = subprocess.run([sys.executable, HOOK_PATH], capture_output=True, text=True, env=env)
    return result

def test_fails_without_mix_exs(temp_project):
    result = run_hook()
    assert result.returncode != 0
    assert "mix.exs not found" in result.stderr.lower()

def test_fails_with_missing_dependencies(temp_project):
    mix_exs = temp_project / "mix.exs"
    mix_exs.write_text('defmodule MyApp.MixProject do\n  def project do\n    [deps: []]\n  end\nend')
    
    result = run_hook()
    assert result.returncode != 0
    assert "missing phoenix dependencies" in result.stderr.lower()

def test_passes_with_phoenix_dependencies(temp_project):
    mix_exs = temp_project / "mix.exs"
    mix_exs.write_text('defmodule MyApp.MixProject do\n  def project do\n    [deps: [{:phoenix, "~> 1.7"}, {:phoenix_ecto, "~> 4.4"}, {:phoenix_live_view, "~> 0.18"}, {:oban, "~> 2.14"}]]\n  end\nend')
    
    # Also need to mock Codex CLI capabilities
    env = os.environ.copy()
    env["CODEX_CAPABILITIES"] = "hooks.v1"
    
    result = run_hook(env=env)
    assert result.returncode == 0

def test_fails_without_codex_capabilities(temp_project):
    mix_exs = temp_project / "mix.exs"
    mix_exs.write_text('defmodule MyApp.MixProject do\n  def project do\n    [deps: [{:phoenix, "~> 1.7"}, {:phoenix_ecto, "~> 4.4"}, {:phoenix_live_view, "~> 0.18"}, {:oban, "~> 2.14"}]]\n  end\nend')
    
    env = os.environ.copy()
    if "CODEX_CAPABILITIES" in env:
        del env["CODEX_CAPABILITIES"]
        
    result = run_hook(env=env)
    assert result.returncode != 0
    assert "codex cli capability" in result.stderr.lower()
