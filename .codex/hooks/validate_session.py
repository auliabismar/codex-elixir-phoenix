import os
import sys
import re
from pathlib import Path

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
        
    print("Environment validation successful.")
    sys.exit(0)

if __name__ == "__main__":
    validate()
