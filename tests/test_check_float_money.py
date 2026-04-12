import pytest
from pathlib import Path
import sys

# Add .codex/hooks to path if needed for direct import
# But for now, we will test the logic directly if we can, 
# or import the function.

# Let's assume the contract is a function: check(tool_name, params, targets) -> violation_data or None

# Mocking the proposed rule structure
import importlib.util

def load_hook_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

HOOK_PATH = Path(".codex/hooks/check_float_money.py")

@pytest.fixture
def rule_module():
    if not HOOK_PATH.exists():
        pytest.skip("Hook module not yet implemented")
    return load_hook_module("check_float_money", HOOK_PATH)

def test_block_float_amount(rule_module):
    """Should block :float for amount field."""
    content = 'field :amount, :float'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/schema.ex"])
    assert violation is not None
    assert "Decimal" in violation["correction"]

def test_block_float_price_in_patch(rule_module):
    """Should block :float for price in a patch."""
    patch = '@@\n-field :price, :decimal\n+field :price, :float'
    violation = rule_module.check("apply_patch", {"patch": patch}, ["lib/schema.ex"])
    assert violation is not None
    assert "price" in violation["reasoning"]

def test_allow_patch_that_removes_float_money(rule_module):
    """Should allow patches that replace money floats with decimals."""
    patch = '@@\n-field :price, :float\n+field :price, :decimal'
    violation = rule_module.check("apply_patch", {"patch": patch}, ["lib/schema.ex"])
    assert violation is None

def test_allow_float_percentage(rule_module):
    """Should allow :float for percentage."""
    content = 'field :completion_percentage, :float'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/schema.ex"])
    assert violation is None

def test_allow_float_coordinates(rule_module):
    """Should allow :float for coordinates."""
    content = 'field :lat, :float\nfield :lng, :float'
    violation = rule_module.check("write_to_file", {"CodeContent": content}, ["lib/schema.ex"])
    assert violation is None

def test_block_float_money_in_new_content(rule_module):
    """Should block supported direct-write keys used by the gateway."""
    content = 'field :amount, :float'
    violation = rule_module.check("write_to_file", {"new_content": content}, ["lib/schema.ex"])
    assert violation is not None

def test_block_float_money_in_migration(rule_module):
    """Should block float money fields in migration DSL too."""
    content = 'add :price, :float'
    violation = rule_module.check(
        "write_to_file",
        {"CodeContent": content},
        ["priv/repo/migrations/20260412000000_create_orders.exs"],
    )
    assert violation is not None
