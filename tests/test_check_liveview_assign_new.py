import sys
from pathlib import Path
import pytest

# Add .codex/hooks to path for direct rule testing
HOOKS_DIR = str(Path(__file__).parent.parent / ".codex" / "hooks")
if HOOKS_DIR not in sys.path:
    sys.path.insert(0, HOOKS_DIR)

from check_liveview_assign_new import check

def test_blocks_volatile_assign_new_in_live_view():
    """Rule should block Repo calls inside assign_new callbacks in LiveViews."""
    params = {
        "TargetFile": "lib/my_app_web/live/user_live.ex",
        "CodeContent": """
        def mount(_params, _session, socket) do
          {:ok, assign_new(socket, :users, fn -> Repo.all(User) end)}
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/live/user_live.ex"])
    assert violation is not None
    assert "assign_new" in violation["reasoning"]
    assert "Repo." in violation["reasoning"]

def test_allows_deterministic_assign_new():
    """Rule should allow simple literals or deterministic defaults."""
    params = {
        "TargetFile": "lib/my_app_web/live/user_live.ex",
        "CodeContent": """
        def mount(_params, _session, socket) do
          {:ok, assign_new(socket, :count, fn -> 0 end)}
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/live/user_live.ex"])
    assert violation is None

def test_allows_non_liveview_assign_new():
    """Rules should not trigger for ordinary modules or function components."""
    params = {
        "TargetFile": "lib/my_app_web/components/core_components.ex",
        "CodeContent": """
        def my_component(assigns) do
          assigns = assign_new(assigns, :id, fn -> "default" end)
          ~H\"\"\"
          <div id={@id}>Content</div>
          \"\"\"
        end
        """
    }
    violation = check("write_to_file", params, ["lib/my_app_web/components/core_components.ex"])
    assert violation is None
