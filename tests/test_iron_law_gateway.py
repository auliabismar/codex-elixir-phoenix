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
    content = GATEWAY_SCRIPT.read_text()
    assert "self.rule_registry =" in content

def test_gateway_blocks_float_money():
    """Gateway should terminate with error on :float amount."""
    payload = {
        "tool": "write_to_file",
        "parameters": {
            "TargetFile": "lib/schema.ex",
            "CodeContent": "field :total_amount, :float"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "total_amount" in stderr

def test_gateway_blocks_float_money_in_new_content():
    """Gateway should scan supported write-content keys beyond CodeContent."""
    payload = {
        "tool": "write_to_file",
        "parameters": {
            "TargetFile": "lib/schema.ex",
            "new_content": "field :amount, :float"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "amount" in stderr

def test_gateway_blocks_float_money_in_migration_dsl():
    """Gateway should block money floats in migrations as well as schemas."""
    payload = {
        "tool": "write_to_file",
        "parameters": {
            "TargetFile": "priv/repo/migrations/20260412000000_create_orders.exs",
            "CodeContent": "add :price, :float"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "price" in stderr

def test_gateway_blocks_string_to_atom():
    """Gateway should terminate with error on dynamic String.to_atom."""
    payload = {
        "tool": "replace_file_content",
        "parameters": {
            "TargetFile": "lib/app.ex",
            "ReplacementContent": 'String.to_atom(user_input)'
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "String.to_existing_atom" in stderr

def test_gateway_blocks_string_to_atom_in_new_str():
    """Gateway should scan supported replace payload keys beyond ReplacementContent."""
    payload = {
        "tool": "replace_file_content",
        "parameters": {
            "TargetFile": "lib/app.ex",
            "new_str": 'String.to_atom(user_input)'
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "String.to_existing_atom" in stderr

def test_gateway_allows_patch_that_removes_float_money():
    """Gateway should allow patches that remediate an existing float money field."""
    payload = {
        "tool": "apply_patch",
        "parameters": {
            "input": "*** Begin Patch\n*** Update File: lib/schema.ex\n@@\n-field :price, :float\n+field :price, :decimal\n*** End Patch\n"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_allows_patch_that_replaces_string_to_atom():
    """Gateway should allow patches that remediate unsafe atom conversion."""
    payload = {
        "tool": "apply_patch",
        "parameters": {
            "input": "*** Begin Patch\n*** Update File: lib/app.ex\n@@\n-String.to_atom(user_input)\n+String.to_existing_atom(user_input)\n*** End Patch\n"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 0
    assert stderr == ""

def test_gateway_blocks_liveview_assign_new_volatile():
    """Gateway should block volatile assign_new in LiveView targets."""
    payload = {
        "tool": "write_to_file",
        "parameters": {
            "TargetFile": "lib/my_app_web/live/data_live.ex",
            "CodeContent": "assign_new(socket, :data, fn -> Repo.get(User, id) end)"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "assign_new" in stderr

def test_gateway_blocks_liveview_unguarded_mount():
    """Gateway should block unguarded Repo calls in LiveView mount."""
    payload = {
        "tool": "write_to_file",
        "parameters": {
            "TargetFile": "lib/my_app_web/live/data_live.ex",
            "CodeContent": "def mount(_params, _session, socket) do users = Repo.all(User) end"
        }
    }
    code, stdout, stderr = run_gateway(payload)
    assert code == 1
    assert "IRON LAW VIOLATION" in stderr
    assert "connected?" in stderr

