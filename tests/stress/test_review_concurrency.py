import pytest
import json
from pathlib import Path
from .stress_utils import MockAgentFactory

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import review_aggregator

def test_review_aggregation_concurrency(stress_runner, repo_root):
    """
    Stress test for ReviewAggregator.
    Simulates many roles being added concurrently.
    """
    import sys
    sys.path.append(str(repo_root / ".codex" / "hooks"))
    import review_aggregator
    
    aggregator = review_aggregator.ReviewAggregator(expected_roles=["role_1", "role_2", "role_3", "role_4"])
    
    def add_finding(idx):
        # Even indices success, odd indices malformed
        role = f"role_{idx}"
        if idx % 2 == 0:
            content = f'<review><finding severity="high"><title>Issue {idx}</title><detail>Detail {idx}</detail><file>file_{idx}.ex</file><recommendation>Fix {idx}</recommendation></finding></review>'
        else:
            content = f'<review><status>timeout</status></review>'
        
        aggregator.add_output(role, content)
        return True

    # Hammer the aggregator with 50 roles
    results = stress_runner(add_finding, iterations=50, max_workers=16, jitter=(0, 0.1))
    
    summary = aggregator.aggregate()
    
    # Verify results
    # 25 successful roles should produce findings
    # 25 timeouts should be in missing_reviewers (if they were expected) or just skipped
    
    findings = summary["checklist"]
    missing = summary["missing_reviewers"]
    
    report = {
        "iterations": 50,
        "findings_count": len(findings),
        "missing_count": len(missing)
    }
    
    report_path = repo_root / "stress-report-review.json"
    with open(report_path, "w") as f:
        json.dump(report, f)
        
    # Since add_output just sets a dict key, and aggregate() is called after everything is added,
    # the main risk is if add_output (dict assignment) or aggregate() itself is not atomic.
    # But in Python, dict assignment is atomic due to GIL.
    # The real test is if we get consistent results.
    # Even indices (25) produce findings, odd indices (25) produce timeouts
    expected_findings = 25
    assert len(findings) == expected_findings, f"Expected {expected_findings} findings, got {len(findings)}"

