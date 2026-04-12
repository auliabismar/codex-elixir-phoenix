import re

# Story 4.4: Background Job Idempotency Guardrails
# Requirement: Deterministic detector for missing unique constraints in Oban workers.

def check(tool_name: str, params: dict, target_files: list[str]) -> dict | None:
    """
    Inspect pending writes for the presence of the unique: configuration option
    inside the use Oban.Worker directive.
    """
    # Keys from iron_law_gateway.py: WRITE_HINT_KEYS + CodeContent/ReplacementContent
    for key in ("CodeContent", "ReplacementContent", "new_content", "new_str", "input", "patch", "content", "replacement"):
        val = params.get(key)
        if isinstance(val, str) and val.strip():
            content = ""
            # For patches, we only care about added lines to avoid blocking deletions or context
            if key == "patch" or (tool_name == "apply_patch" and key in ("input", "content")):
                # Exclude diff headers
                added_lines = [line[1:] for line in val.splitlines() if line.startswith("+") and not line.startswith("+++")]
                content = "\n".join(added_lines) + "\n"
            else:
                content = val + "\n"
            
            if not content.strip():
                continue
                
            # Bypass mechanism
            if "# codex-disable: require_oban_idempotency" in content:
                continue
                
            # Strip simple line comments
            code_without_comments = re.sub(r"#.*", "", content)

            # Detect 'use Oban.Worker' in the added/modified content
            if re.search(r"use\s+Oban\.Worker", code_without_comments):
                # Ensure unique: [keys: ...] is present
                if not re.search(r"unique\s*:\s*\[\s*keys\s*:", code_without_comments):
                    return {
                        "reasoning": "IRON LAW VIOLATION: Oban worker detected without idempotency protection. Missing 'unique: [keys: ...]' configuration.",
                        "correction": "Mandatory: add 'unique: [keys: [...], period: ...]' to your 'use Oban.Worker' statement to prevent duplicate job execution."
                    }

    return None
