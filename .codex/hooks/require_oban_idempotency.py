import re
import iron_law_utils

# Story 4.4: Background Job Idempotency Guardrails
# Refactored to use iron_law_utils (Epic 4 Action Item)

def check(tool_name: str, params: dict, target_files: list[str]) -> dict | None:
    """
    Inspect pending writes for the presence of the unique: configuration option
    inside the use Oban.Worker directive.
    """
    # Fix: Pass tool_name to correctly extract from 'patch' if needed
    content = iron_law_utils.extract_content(params, tool_name)
    if not content.strip():
        return None

    # Bypass mechanism
    if "# codex-disable: require_oban_idempotency" in content:
        return None
        
    # Strip simple line comments
    code_without_comments = re.sub(r"#.*", "", content)

    # Detect 'use Oban.Worker' in the added/modified content
    # Use the more robust is_oban_worker which should ideally use regex
    if iron_law_utils.is_oban_worker(code_without_comments):
        # Ensure unique: [keys: ...] is present
        if not re.search(r"unique\s*:\s*\[\s*keys\s*:", code_without_comments):
            return {
                "reasoning": "IRON LAW VIOLATION: Oban worker detected without idempotency protection. Missing 'unique: [keys: ...]' configuration.",
                "correction": "Mandatory: add 'unique: [keys: [...], period: ...]' to your 'use Oban.Worker' statement to prevent duplicate job execution."
            }

    return None
