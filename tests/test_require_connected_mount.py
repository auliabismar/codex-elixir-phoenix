import sys
from pathlib import Path
import pytest

# Add .codex/hooks to path for direct rule testing
HOOKS_DIR = str(Path(__file__).parent.parent / ".codex" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from require_connected_mount import check

def test_blocks_unguarded_query_in_mount():
    """Rule should block direct Repo calls in mount/3 that lack connected? guards."""
    params = {
        "TargetFile": "lib/my_app_web/live/user_live.ex",
        "CodeContent": """
        def mount(_params, _session, socket) do
          users = Repo.all(User)
          {:ok, assign(socket, :users, users)}
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/live/user_live.ex"])
    assert violation is not None
    assert "connected?(socket)" in violation["correction"]

def test_allows_guarded_query_in_mount():
    """Rule should allow Repo calls if they are inside a connected? check."""
    params = {
        "TargetFile": "lib/my_app_web/live/user_live.ex",
        "CodeContent": """
        def mount(_params, _session, socket) do
          if connected?(socket) do
            users = Repo.all(User)
            {:ok, assign(socket, :users, users)}
          else
            {:ok, assign(socket, :users, [])}
          end
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/live/user_live.ex"])
    assert violation is None

def test_allows_unguarded_non_query_work():
    """Rule should allow lightweight non-DB work in mount/3."""
    params = {
        "TargetFile": "lib/my_app_web/live/user_live.ex",
        "CodeContent": """
        def mount(_params, _session, socket) do
          {:ok, assign(socket, :page_title, "Users")}
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/live/user_live.ex"])
    assert violation is None
