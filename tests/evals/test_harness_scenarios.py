import json
import textwrap
from pathlib import Path

# Story 7.1: Failure Simulation Scenarios

def _parse_child_json(result):
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def _write_mix_exs(project_root: Path):
    (project_root / "mix.exs").write_text(
        'defmodule EvalApp.MixProject do\n'
        '  use Mix.Project\n'
        '  def project, do: [app: :eval_app, version: "0.1.0"]\n'
        'end\n',
        encoding="utf-8",
    )


def test_tidewave_timeout_handling(python_runner):
    """Ensure validate_session handles Tidewave probe timeouts gracefully."""
    script = textwrap.dedent(
        """
        import json
        import sys
        import validate_session

        validate_session.load_tidewave_command = lambda: [
            sys.executable,
            "-c",
            "import time; time.sleep(1)",
        ]

        message, is_available = validate_session.detect_tidewave_status(timeout_seconds=0.1)
        print(json.dumps({"message": message, "available": is_available}))
        """
    )

    data = _parse_child_json(python_runner(script))
    assert "timed out" in data["message"]
    assert data["available"] is False


def test_tidewave_crash_handling(python_runner):
    """Ensure validate_session handles Tidewave probe crashes/missing binary."""
    script = textwrap.dedent(
        """
        import json
        import validate_session

        validate_session.load_tidewave_command = lambda: ["missing-tidewave-binary"]

        message, is_available = validate_session.detect_tidewave_status()
        print(json.dumps({"message": message, "available": is_available}))
        """
    )

    data = _parse_child_json(python_runner(script))
    assert "command not found" in data["message"]
    assert data["available"] is False


def test_validate_compilation_missing_mix_binary(temp_project, python_runner):
    """Ensure validate_compilation fails correctly if mix binary is missing."""
    _write_mix_exs(temp_project)
    script = textwrap.dedent(
        """
        import json
        from pathlib import Path
        import validate_compilation

        print(json.dumps(validate_compilation.validate_project(Path.cwd())))
        """
    )

    data = _parse_child_json(python_runner(script, cwd=temp_project, env={"PATH": ""}))
    assert data["success"] is False
    assert data["error_type"] == "toolchain"
    assert "not found" in data["logs"].lower()


def test_validate_compilation_fail_exit_code(temp_project, python_runner):
    """Ensure validate_compilation reports failure if mix compile returns non-zero."""
    _write_mix_exs(temp_project)
    (temp_project / "mix.cmd").write_text(
        "@echo off\r\n"
        "if \"%1\"==\"compile\" (\r\n"
        "  echo Compilation error 1>&2\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        "exit /b 0\r\n",
        encoding="utf-8",
    )

    script = textwrap.dedent(
        """
        import json
        from pathlib import Path
        import validate_compilation

        print(json.dumps(validate_compilation.validate_project(Path.cwd())))
        """
    )

    data = _parse_child_json(
        python_runner(script, cwd=temp_project, path_prepend=temp_project)
    )
    assert data["success"] is False
    assert data["error_type"] == "compilation"
    assert "Compilation error" in data["logs"]
