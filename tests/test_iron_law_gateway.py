import json
import subprocess
import sys
from pathlib import Path
import pytest

# Paths relative to repo root
HOOKS_JSON = Path(".codex/hooks.json")
GATEWAY_SCRIPT = Path(".codex/hooks/iron_law_gateway.py")

def test_hooks_json_wiring():
    """Verify hooks.json contains both SessionStart and PreToolUse."""
    assert HOOKS_JSON.exists()
    content = json.loads(HOOKS_JSON.read_text())
    
    assert "SessionStart" in content
    assert "PreToolUse" in content
    
    pre_tool_use = content["PreToolUse"]
    assert isinstance(pre_tool_use, list)
    assert any(h["path"] == "hooks/iron_law_gateway.py" for h in pre_tool_use)

def run_gateway(payload):
    """Helper to run the gateway script with a JSON payload."""
    process = subprocess.Popen(
        [sys.executable, str(GATEWAY_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input=json.dumps(payload))
    return process.returncode, stdout, stderr

def test_gateway_fast_path_allowed():
    """Unrelated files should pass through (return 0)."""
    payload = {
        "tool": "write_to_file",
        "parameters": {"TargetFile": "README.md"}
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_elixir_intercept_no_rules():
    """Elixir files should pass when no rules are registered."""
    payload = {
        "tool": "replace_file_content",
        "parameters": {"TargetFile": "lib/app.ex"}
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_malformed_payload():
    """Malformed JSON should fail closed."""
    process = subprocess.Popen(
        [sys.executable, str(GATEWAY_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = process.communicate(input="not json")
    assert process.returncode == 1
    assert "IRON LAW VIOLATION: Malformed hook payload" in stderr

def test_gateway_missing_fields_fail_closed():
    """Unknown payload shapes should fail closed with actionable output."""
    payload = {"other": "data"}
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION: Missing tool name in hook payload" in stderr

def test_gateway_non_write_tool_ignored():
    """Non-write tool events should bypass the gateway even for Elixir paths."""
    payload = {
        "tool": "read_file",
        "parameters": {"path": "lib/app.ex"}
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_apply_patch_detects_elixir_targets():
    """Patch-based writes to Elixir files should route through the dispatcher."""
    payload = {
        "tool": "apply_patch",
        "parameters": {
            "input": "*** Begin Patch\n*** Update File: lib/app.ex\n@@\n-old\n+new\n*** End Patch\n"
        },
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_malformed_tool_args_fail_closed():
    """Stringified tool arguments must be valid JSON."""
    payload = {
        "tool": "write_to_file",
        "toolArgs": "{not-json}",
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION: Malformed tool parameters" in stderr

def test_gateway_rule_registry_exists():
    """Verify the class has a rule_registry attribute for later expansion."""
    # We can't easily import the script directly if it has side effects on import,
    # but we can check if it defines the attribute.
    content = GATEWAY_SCRIPT.read_text()
    assert "self.rule_registry =" in content
