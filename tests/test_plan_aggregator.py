"""
tests/test_plan_aggregator.py

Tests for the plan aggregator module (.codex/hooks/plan_aggregator.py).
"""

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from plan_aggregator import PlanAggregator, aggregate_discovery_outputs, parse_discovery_xml


@pytest.fixture
def aggregator():
    return PlanAggregator()


def test_add_discovery(aggregator):
    aggregator.add_discovery("ecto-schema-analyzer", "Schema: User\nFields: id, email")
    assert len(aggregator.discoveries) == 1
    assert aggregator.discoveries[0].role == "ecto-schema-analyzer"


def test_aggregate_empty(aggregator):
    result = aggregator.aggregate()
    # Should now contain error blocks for missing roles
    assert "ERROR: Discovery agent failed" in result


def test_aggregate_multiple_discoveries(aggregator):
    aggregator.add_discovery("ecto-schema-analyzer", "Schema: User\nFields: id, email")
    aggregator.add_discovery("phoenix-router-mapper", "Routes:\n/users GET")
    
    result = aggregator.aggregate()
    
    assert '<discovery role="ecto-schema-analyzer">' in result
    assert '<discovery role="phoenix-router-mapper">' in result
    assert "</discovery>" in result


def test_aggregate_discovery_outputs_function():
    outputs = {
        "ecto-schema-analyzer": "Schema: User",
        "phoenix-router-mapper": "Routes:\n/users",
        "liveview-component-scanner": "LiveViews: UserLive",
        "dependency-auditor": "Deps: phoenix",
    }
    
    result = aggregate_discovery_outputs(outputs)
    
    assert '<discovery role="ecto-schema-analyzer">' in result
    assert '<discovery role="phoenix-router-mapper">' in result
    assert '<discovery role="liveview-component-scanner">' in result
    assert '<discovery role="dependency-auditor">' in result


def test_parse_discovery_xml():
    xml_input = '''
<discovery role="ecto-schema-analyzer">
Schema: User
Fields: id, email
</discovery>

<discovery role="phoenix-router-mapper">
Routes: /users
</discovery>
'''
    
    result = parse_discovery_xml(xml_input)
    
    assert "ecto-schema-analyzer" in result
    assert "phoenix-router-mapper" in result
    assert "Schema: User" in result["ecto-schema-analyzer"]
    assert "Routes: /users" in result["phoenix-router-mapper"]


def test_get_role_content(aggregator):
    aggregator.add_discovery("ecto-schema-analyzer", "Content A")
    aggregator.add_discovery("phoenix-router-mapper", "Content B")
    
    assert aggregator.get_role_content("ecto-schema-analyzer") == "Content A"
    assert aggregator.get_role_content("phoenix-router-mapper") == "Content B"
    assert aggregator.get_role_content("nonexistent") is None


def test_resolve_conflicts(aggregator):
    # Use real-world-like Elixir route/component findings
    aggregator.add_discovery("phoenix-router-mapper", "Route: users_path = /users\nRoute: user_path = /users/:id")
    aggregator.add_discovery("liveview-component-scanner", "Component: UsersLive at /users\nComponent: UserLive at /users/:id")
    
    resolutions = aggregator.resolve_conflicts()
    assert len(resolutions) >= 1
    assert any("user_path" in resolution for resolution in resolutions)


def test_xml_escaping(aggregator):
    bad_content = "Something <with> tags and & ampersands or </discovery> closures."
    aggregator.add_discovery("ecto-schema-analyzer", bad_content)
    result = aggregator.aggregate()
    
    # Should be escaped in XML block
    assert "&lt;with&gt;" in result
    assert "&amp;" in result
    assert "&lt;/discovery&gt;" in result
    
    # Should be unescapable
    from plan_aggregator import parse_discovery_xml
    parsed = parse_discovery_xml(result)
    assert parsed["ecto-schema-analyzer"] == bad_content


def test_missing_role_backfill(aggregator):
    # Only adding one role
    aggregator.add_discovery("ecto-schema-analyzer", "Schema: User")
    result = aggregator.aggregate()
    
    # Check that missing roles were backfilled with error blocks
    assert '<discovery role="phoenix-router-mapper">' in result
    assert "ERROR: Discovery agent failed" in result


def test_role_normalization(aggregator):
    aggregator.add_discovery("phoenix_router_mapper", "content")
    assert aggregator.get_role_content("phoenix-router-mapper") == "content"
    assert aggregator.get_role_content("phoenix_router_mapper") == "content"
