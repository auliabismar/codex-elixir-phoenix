import pytest
from pathlib import Path
from tests.benchmarks.benchmark_utils import MetricsAggregator, BenchmarkRunner, compute_similarity

ORACLE_PROMPTS = {
    "complex_ecto_preload": "Implement a complex Ecto preload with nested associations including user, posts with comments and authors. Use preload/2 with nested keyword syntax.",
    "liveview_js_hook": "Implement a LiveView component with a JavaScript hook integration. Use phx-hook attribute in the template and define the hook module.",
    "oban_idempotent_worker": "Implement an idempotent Oban worker with unique constraints based on args and worker fields. Use the unique option with period of 60 seconds.",
}

@pytest.fixture
def aggregator():
    return MetricsAggregator()


@pytest.fixture
def runner(aggregator, python_runner, temp_project, agent_scope):
    return BenchmarkRunner(aggregator, python_runner, temp_project, agent_scope)


def test_quality_benchmarking_harness(runner, aggregator, repo_root):
    """
    Executes the benchmarking harness across a set of golden prompts.
    """
    from tests.benchmarks.benchmark_utils import Reporter

    oracles_dir = repo_root / "tests" / "benchmarks" / "oracles"
    oracle_files = list(oracles_dir.glob("*.ex"))

    assert len(oracle_files) >= 3, f"Expected at least 3 oracle files, found {len(oracle_files)}"

    for oracle_file in oracle_files:
        case_id = oracle_file.stem.upper()
        oracle_code = oracle_file.read_text()
        golden_prompt = ORACLE_PROMPTS.get(oracle_file.stem, f"Implement {case_id} logic in Elixir.")

        assert oracle_code.strip(), f"Oracle file {oracle_file.name} is empty"

        runner.run_case(case_id, golden_prompt, oracle_code, "baseline", golden_prompt=golden_prompt)
        runner.run_case(case_id, golden_prompt, oracle_code, "phoenix", golden_prompt=golden_prompt)

    report = aggregator.generate_report()

    assert len(report.results) == len(oracle_files) * 2

    assert report.summary.get("phoenix", {}).get("success_rate", 0) >= 0.5, "Phoenix should achieve at least 50% success rate"

    output_dir = repo_root / "tests" / "benchmarks" / "output"
    output_dir.mkdir(exist_ok=True)
    report.to_json(output_dir / "benchmark-report.json")
    reporter = Reporter(report)
    reporter.generate_markdown_summary(output_dir / "benchmarks-summary.md")