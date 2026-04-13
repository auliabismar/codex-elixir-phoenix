"""
tests/test_review_aggregator.py

Tests for the parallel $phx-review aggregation helper (.codex/hooks/review_aggregator.py).
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from review_aggregator import aggregate_review_outputs  # noqa: E402


def test_collapses_duplicate_findings_and_keeps_highest_severity():
    outputs = {
        "idiom": """
<review role="idiom">
  <finding severity="medium">
    <title>Large function in context module</title>
    <detail>Function exceeds maintainability threshold.</detail>
    <file>lib/app/accounts.ex</file>
    <recommendation>Split logic into smaller private helpers.</recommendation>
  </finding>
</review>
""",
        "architecture": """
<review role="architecture">
  <finding severity="high">
    <title>Large function in context module</title>
    <detail>Function exceeds maintainability threshold.</detail>
    <file>lib/app/accounts.ex</file>
    <recommendation>Split logic into smaller private helpers.</recommendation>
  </finding>
</review>
""",
        "security": """
<review role="security">
  <finding severity="low">
    <title>Improve session cookie options</title>
    <detail>Consider tightening same_site policy.</detail>
    <file>lib/app_web/endpoint.ex</file>
    <recommendation>Use strict policy where compatible.</recommendation>
  </finding>
</review>
""",
        "performance": """
<review role="performance">
  <finding severity="medium">
    <title>Potential N+1 query in dashboard loader</title>
    <detail>Associated records are loaded in a loop.</detail>
    <file>lib/app/dashboard.ex</file>
    <recommendation>Preload associations before iterating.</recommendation>
  </finding>
</review>
""",
    }

    result = aggregate_review_outputs(outputs)
    checklist = result["checklist"]

    assert len(checklist) == 3
    merged = checklist[0]
    assert merged["title"] == "Large function in context module"
    assert merged["severity"] == "high"
    assert merged["reviewers"] == ["architecture", "idiom"]


def test_backfills_missing_and_timeout_reviewers():
    outputs = {
        "idiom": """
<review role="idiom">
  <finding severity="low">
    <title>Prefer with-chain for nested branching</title>
    <detail>Pattern matching can simplify the control flow.</detail>
    <file>lib/app/workflow.ex</file>
    <recommendation>Refactor nested case statements into a with block.</recommendation>
  </finding>
</review>
""",
        "security": """
<review role="security">
  <status>timeout</status>
</review>
""",
    }

    result = aggregate_review_outputs(outputs)
    checklist = result["checklist"]
    titles = [item["title"] for item in checklist]

    assert "Reviewer unavailable: performance" in titles
    assert "Reviewer unavailable: security" in titles
    assert "Reviewer unavailable: architecture" in titles
    assert result["missing_reviewers"] == ["architecture", "performance", "security"]


def test_parses_nested_review_payload_from_parallel_wrapper():
    outputs = {
        "idiom": """
<review role="idiom">
  <review role="idiom">
    <finding severity="high">
      <title>Nested wrapper finding</title>
      <detail>Wrapped reviewer output should still be parsed.</detail>
      <file>lib/app/accounts.ex</file>
      <recommendation>Flatten or unwrap the nested review payload.</recommendation>
    </finding>
  </review>
</review>
""",
        "security": '<review role="security"><status>clean</status></review>',
        "performance": '<review role="performance"><status>clean</status></review>',
        "architecture": '<review role="architecture"><status>clean</status></review>',
    }

    result = aggregate_review_outputs(outputs)

    assert result["missing_reviewers"] == []
    assert result["total_findings"] == 1
    assert result["checklist"][0]["title"] == "Nested wrapper finding"
    assert result["checklist"][0]["severity"] == "high"
    assert result["checklist"][0]["reviewers"] == ["idiom"]


def test_orders_checklist_by_severity_then_title():
    outputs = {
        "idiom": """
<review role="idiom">
  <finding severity="low">
    <title>z-finding</title>
    <detail>low</detail>
    <recommendation>low</recommendation>
  </finding>
</review>
""",
        "security": """
<review role="security">
  <finding severity="high">
    <title>b-finding</title>
    <detail>high</detail>
    <recommendation>high</recommendation>
  </finding>
</review>
""",
        "performance": """
<review role="performance">
  <finding severity="high">
    <title>a-finding</title>
    <detail>high</detail>
    <recommendation>high</recommendation>
  </finding>
</review>
""",
        "architecture": """
<review role="architecture">
  <finding severity="medium">
    <title>m-finding</title>
    <detail>medium</detail>
    <recommendation>medium</recommendation>
  </finding>
</review>
""",
    }

    result = aggregate_review_outputs(outputs)
    ordered_titles = [item["title"] for item in result["checklist"]]

    assert ordered_titles == ["a-finding", "b-finding", "m-finding", "z-finding"]
