from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add .codex/hooks to sys.path
hooks_path = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.append(str(hooks_path))

import validate_compilation  # type: ignore


def test_validate_compilation_success():
    """Test that it returns success when mix commands succeed."""
    with patch("validate_compilation.shutil.which", return_value="C:/Elixir/bin/mix.bat"), patch(
        "validate_compilation.subprocess.run"
    ) as mock_run:
        # Mock successful runs for compile and format
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        result = validate_compilation.validate_project(Path("."))

        assert result["success"] is True
        assert mock_run.call_count == 2
        first_call = mock_run.call_args_list[0]
        assert first_call.args[0] == ["C:/Elixir/bin/mix.bat", "compile", "--warnings-as-errors"]
        assert first_call.kwargs["cwd"] == str(Path(".").resolve())
        assert first_call.kwargs["check"] is False
        assert first_call.kwargs.get("shell", False) is False


def test_validate_compilation_failure():
    """Test that it returns failure when mix compile fails."""
    with patch("validate_compilation.shutil.which", return_value="C:/Elixir/bin/mix.bat"), patch(
        "validate_compilation.subprocess.run"
    ) as mock_run:
        # Mock failed compilation
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Compiling...",
            stderr="error: undefined function\n" * 60,
        )

        result = validate_compilation.validate_project(Path("."))

        assert result["success"] is False
        assert "compilation" in result["error_type"]
        # Should include last 50 lines of crash logs
        assert len(result["logs"].splitlines()) <= 50
        assert "error: undefined function" in result["logs"]


def test_validate_format_failure():
    """Test that it returns failure when mix format fails."""
    with patch("validate_compilation.shutil.which", return_value="C:/Elixir/bin/mix.bat"), patch(
        "validate_compilation.subprocess.run"
    ) as mock_run:
        # First call (compile) succeeds, second (format) fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="Compiled", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="mix format failed"),
        ]

        result = validate_compilation.validate_project(Path("."))

        assert result["success"] is False
        assert "format" in result["error_type"]
        assert "mix format failed" in result["logs"]


def test_validate_missing_mix_toolchain():
    """Test that missing Mix is surfaced as an environment failure."""
    with patch("validate_compilation.shutil.which", return_value=None), patch(
        "validate_compilation.subprocess.run"
    ) as mock_run:
        result = validate_compilation.validate_project(Path("."))

        assert result["success"] is False
        assert result["error_type"] == "toolchain"
        assert "not found on PATH" in result["logs"]
        mock_run.assert_not_called()
