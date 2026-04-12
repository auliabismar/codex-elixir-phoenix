import pytest
from pathlib import Path
import sys
import importlib.util

def load_hook_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

HOOK_PATH = Path(".codex/hooks/block_string_to_atom.py")

@pytest.fixture
def rule_module():
    if not HOOK_PATH.exists():
        pytest.skip("Hook module not yet implemented")
    return load_hook_module("block_string_to_atom", HOOK_PATH)

def test_block_dynamic_string_to_atom(rule_module):
    """Should block dynamic String.to_atom usage."""
    content = 'String.to_atom(variable_name)'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/app.ex"])
    assert violation is not None
    assert "String.to_existing_atom" in violation["correction"]

def test_block_interpolated_string_to_atom(rule_module):
    """Should block interpolated String.to_atom."""
    content = 'String.to_atom("prefix_#{id}")'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/app.ex"])
    assert violation is not None

def test_allow_string_to_existing_atom(rule_module):
    """Should allow String.to_existing_atom."""
    content = 'String.to_existing_atom(input)'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/app.ex"])
    assert violation is None

def test_block_map_access_to_atom(rule_module):
    """Should block map access in String.to_atom."""
    content = 'String.to_atom(params["type"])'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/app.ex"])
    assert violation is not None

def test_block_string_to_atom_in_new_str(rule_module):
    """Should block supported direct-write keys used by replace operations."""
    content = 'String.to_atom(user_input)'
    violation = rule_module.check("replace_file_content", {"new_str": content}, ["lib/app.ex"])
    assert violation is not None

def test_allow_patch_that_replaces_with_existing_atom(rule_module):
    """Should allow patches that remove unsafe atom conversion."""
    patch = '@@\n-String.to_atom(user_input)\n+String.to_existing_atom(user_input)'
    violation = rule_module.check("apply_patch", {"patch": patch}, ["lib/app.ex"])
    assert violation is None
