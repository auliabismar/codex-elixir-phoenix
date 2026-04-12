import sys
from pathlib import Path

# Add the hooks directory to path
hooks_dir = Path(__file__).parent.parent / ".codex" / "hooks"
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from require_oban_idempotency import check

def test_oban_worker_missing_unique_blocked():
    """Oban workers must have unique: configuration."""
    params = {
        "CodeContent": "defmodule MyApp.Worker do\n  use Oban.Worker, queue: :events\nend"
    }
    violation = check("write_to_file", params, ["lib/my_app/worker.ex"])
    assert violation is not None
    assert "IRON LAW VIOLATION" in violation["reasoning"]
    assert "unique:" in violation["correction"]

def test_oban_worker_with_unique_allowed():
    """Oban workers with unique: configuration should pass."""
    params = {
        "CodeContent": "defmodule MyApp.Worker do\n  use Oban.Worker, queue: :events, unique: [keys: [:id], period: 60]\nend"
    }
    violation = check("write_to_file", params, ["lib/my_app/worker.ex"])
    assert violation is None

def test_oban_worker_missing_keys_blocked():
    """Oban workers with unique: but missing keys: should be blocked."""
    params = {
        "CodeContent": "defmodule MyApp.Worker do\n  use Oban.Worker, queue: :events, unique: true\nend"
    }
    violation = check("write_to_file", params, ["lib/my_app/worker.ex"])
    assert violation is not None
    assert "IRON LAW VIOLATION" in violation["reasoning"]

def test_non_worker_module_allowed():
    """Regular modules without Oban.Worker should pass."""
    params = {
        "CodeContent": "defmodule MyApp.Utils do\n  def help, do: :ok\nend"
    }
    violation = check("write_to_file", params, ["lib/my_app/utils.ex"])
    assert violation is None

def test_oban_worker_as_patch_blocked():
    """Oban workers added via patch must also have unique:."""
    params = {
        "patch": "@@ -1,3 +1,6 @@\n+defmodule MyApp.Worker do\n+  use Oban.Worker, queue: :default\n+end"
    }
    violation = check("apply_patch", params, ["lib/my_app/worker.ex"])
    assert violation is not None
    assert "unique:" in violation["correction"]

def test_oban_worker_as_patch_allowed():
    """Oban workers added via patch with unique: should pass."""
    params = {
        "patch": "@@ -1,3 +1,6 @@\n+defmodule MyApp.Worker do\n+  use Oban.Worker, unique: [keys: [:user_id]]\n+end"
    }
    violation = check("apply_patch", params, ["lib/my_app/worker.ex"])
    assert violation is None

def test_oban_worker_bypass_allowed():
    """Oban workers with bypass comment should pass."""
    params = {
        "CodeContent": "defmodule MyApp.Worker do\n  # codex-disable: require_oban_idempotency\n  use Oban.Worker, queue: :default\nend"
    }
    violation = check("write_to_file", params, ["lib/my_app/worker.ex"])
    assert violation is None

def test_oban_worker_cross_patch_contamination():
    """Multiple parameters should be evaluated independently."""
    params = {
        "CodeContent": "defmodule MyApp.Worker do\n  use Oban.Worker, queue: :events\nend",
        "ReplacementContent": "unique: [keys: [:id]]"
    }
    violation = check("write_to_file", params, ["lib/my_app/worker.ex"])
    assert violation is not None
