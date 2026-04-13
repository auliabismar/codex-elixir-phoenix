import os
import sys
import re
import subprocess
import tomllib
from pathlib import Path

TIDEWAVE_TIMEOUT_SECONDS = 5


def load_tidewave_command():
    agent_dir = Path(__file__).resolve().parent.parent / "agents"

    for agent_file in sorted(agent_dir.glob("*.toml")):
        data = tomllib.loads(agent_file.read_text(encoding="utf-8"))
        tidewave = data.get("mcp_servers", {}).get("tidewave")
        if not tidewave:
            continue

        command = tidewave.get("command")
        args = tidewave.get("args", [])
        if command:
            return [command, *args]

    return None


def detect_tidewave_status(timeout_seconds=TIDEWAVE_TIMEOUT_SECONDS):
    command = load_tidewave_command()
    if not command:
        return "Tidewave MCP: No Tidewave server configuration found. Introspection will be limited."

    command_display = " ".join(command)
    probe_command = [*command, "--help"]

    try:
        result = subprocess.run(
            probe_command,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return f"Tidewave MCP: Transport command not found ({command[0]}). Introspection will be limited."
    except subprocess.TimeoutExpired:
        return (
            f"Tidewave MCP: Availability probe timed out for {command_display} "
            f"after {timeout_seconds}s. Introspection will be limited."
        )
    except OSError as exc:
        return f"Tidewave MCP: Availability probe failed for {command_display} ({exc}). Introspection will be limited."

    if result.returncode == 0:
        return f"Tidewave MCP: Server command is available ({command_display})."

    return f"Tidewave MCP: Server command is unavailable ({command_display}). Introspection will be limited."


def validate():
    cwd = Path.cwd()
    mix_exs_path = cwd / "mix.exs"
    
    # 1. Check for mix.exs
    if not mix_exs_path.exists():
        print("Error: mix.exs not found. This plugin requires a Phoenix project.", file=sys.stderr)
        sys.exit(1)
        
    # 2. Check for dependencies
    content = mix_exs_path.read_text(encoding="utf-8", errors="ignore")
    required_deps = ["phoenix", "phoenix_ecto", "phoenix_live_view", "oban"]
    missing_deps = []
    
    for dep in required_deps:
        if not re.search(rf":{dep}\b", content):
            missing_deps.append(dep)
            
    if missing_deps:
        print(f"Error: Missing Phoenix dependencies in mix.exs: {', '.join(missing_deps)}", file=sys.stderr)
        sys.exit(1)
        
    # 3. Check for Codex CLI capabilities
    capabilities = os.environ.get("CODEX_CAPABILITIES", "")
    cap_list = [c.strip() for c in capabilities.replace(",", " ").split()]
    if "hooks.v1" not in cap_list:
        print("Error: Codex CLI capability 'hooks.v1' is required for this plugin.", file=sys.stderr)
        sys.exit(1)

    # 4. Detect Tidewave MCP availability (STORY 6.1)
    print(detect_tidewave_status())
        
    print("Environment validation successful.")
    sys.exit(0)

if __name__ == "__main__":
    validate()
