import json
import os
import subprocess
import sys
import psutil
import pytest
from pathlib import Path
from .stress_utils import MockAgentFactory, AuditPlan

def test_planning_concurrency_stress(temp_project, stress_runner, repo_root):
    """
    Intensive stress test for planning concurrency.
    """
    from .stress_utils import AuditPlan
    import json
    
    plan_slug = "stress-max-load"
    plan_dir = temp_project / ".codex" / "plans" / plan_slug
    plan_dir.mkdir(parents=True)
    plan_path = plan_dir / "plan.md"
    
    # Plan with 110 tasks (to allow for 100 iterations + padding)
    tasks = [f"Stress Task {i}" for i in range(110)]
    tasks_md = "\n".join([f"- [ ] {t}" for t in tasks])
    
    plan_path.write_text(f"# Stress Load\n\n## Goal\nLoad test.\n\n## Tasks\n\n{tasks_md}\n\n## Notes\nN/A\n", encoding="utf-8")

    def run_mark_complete(idx):
        script = f"""
import sys
from pathlib import Path
sys.path.append(r"{repo_root / '.codex' / 'hooks'}")
import plan_state
plan_path = Path(r"{plan_path}")
plan_state.mark_task_complete(plan_path, 8 + {idx})
"""
        import subprocess
        return subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)

    # 100 iterations, 8 workers with jitter 100ms-2s per spec AC #2
    iterations = 100
    process = psutil.Process()
    start_mem = process.memory_info().rss / 1024 / 1024  # MB
    results = stress_runner(run_mark_complete, iterations=iterations, max_workers=8, jitter=(0.1, 2.0))
    peak_mem = process.memory_info().rss / 1024 / 1024  # MB
    
    content = plan_path.read_text(encoding="utf-8")
    audit = AuditPlan.check_integrity(content)
    done_count = content.count("- [x]")
    
    success_rate = (done_count / iterations) * 100
    
    report = {
        "test_name": "planning_concurrency_stress",
        "iterations": iterations,
        "success_count": done_count,
        "success_rate_percent": success_rate,
        "audit_passed": audit["valid"],
        "issues": audit["issues"],
        "bottleneck": "PlanState Load-Modify-Store Race Condition" if success_rate < 100 else "None detected",
        "memory_usage_mb": {"start": start_mem, "peak": peak_mem}
    }
    
    # Save to project root as requested by story
    report_path = repo_root / "stress-report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\nStress Report generated at {report_path}")
    print(f"Success Rate: {success_rate}%")
    
    assert audit["valid"], f"Plan corruption: {audit['issues']}"
    assert done_count <= iterations, f"Cannot have more completions ({done_count}) than iterations ({iterations})"
    assert success_rate > 95, f"Success rate too low: {success_rate}%"
