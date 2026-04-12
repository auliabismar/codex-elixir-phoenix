import shutil
import subprocess
from pathlib import Path


def validate_project(repo_root: Path) -> dict:
    """
    Executes Elixir compilation and formatting checks.

    Returns:
        dict: {
            "success": bool,
            "error_type": str | None, ("compilation", "format", or "toolchain")
            "logs": str | None
        }
    """
    repo_root = Path(repo_root).resolve()
    mix_executable = shutil.which("mix")
    if mix_executable is None:
        return _build_failure("toolchain", "Mix executable not found on PATH.")

    # 1. Compilation check
    compile_res = _run_mix(repo_root, mix_executable, "compile", "--warnings-as-errors")
    if compile_res.returncode != 0:
        logs = _extract_logs(compile_res)
        return _build_failure(
            "toolchain" if _looks_like_toolchain_failure(logs) else "compilation",
            logs,
        )

    # 2. Format check
    format_res = _run_mix(repo_root, mix_executable, "format", "--check-formatted")
    if format_res.returncode != 0:
        logs = _extract_logs(format_res)
        return _build_failure(
            "toolchain" if _looks_like_toolchain_failure(logs) else "format",
            logs,
        )

    return {
        "success": True,
        "error_type": None,
        "logs": None,
    }


def _run_mix(repo_root: Path, mix_executable: str, *args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [mix_executable, *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return subprocess.CompletedProcess(
            [mix_executable, *args],
            returncode=1,
            stdout="",
            stderr=str(exc),
        )


def _build_failure(error_type: str, logs: str) -> dict:
    return {
        "success": False,
        "error_type": error_type,
        "logs": _get_last_n_lines(logs, 50),
    }


def _extract_logs(result: subprocess.CompletedProcess[str]) -> str:
    return result.stderr or result.stdout or ""


def _looks_like_toolchain_failure(logs: str) -> bool:
    normalized = logs.lower()
    markers = (
        "not recognized as an internal or external command",
        "command not found",
        "no such file or directory",
        "the system cannot find the file specified",
    )
    return any(marker in normalized for marker in markers)


def _get_last_n_lines(text: str, n: int) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[-n:])
