import re
from liveview_utils import _iter_candidate_content, _is_liveview

# Story 4.3: Phoenix LiveView Architectural Guardrails - assign_new protection
# Contract: check(tool_name: str, params: dict, targets: list[str]) -> dict | None

# Simplified match that finds assign_new calls inside mount functions
# Scope to mount/3: Look for def mount(...) do ... end
MOUNT_PATTERN = re.compile(
    r"def\s+mount\b.*?\bdo\b(.*?)(?=\ndef\s|$)",
    re.DOTALL
)

# Robust assign_new pattern: captures the function reference or tuple
ASSIGN_NEW_PATTERN = re.compile(
    r"assign_new\s*\([^,]+,\s*:[a-zA-Z0-9_]+\s*,\s*(fn\b.*?->.*?end|&[a-zA-Z0-9_./]+|\{[A-Z][a-zA-Z0-9_.]*,\s*:[a-zA-Z0-9_]+\s*,\s*\[.*?\]\})",
    re.DOTALL
)

# Volatile indicators: Repo calls, contexts that imply DB fetch, DateTime, random
VOLATILE_INDICATORS = [
    r"Repo\.",
    r"\b[A-Z][a-zA-Z0-9_]*\.(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
    r"\b(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
    r"DateTime\.",
    r"Time\.",
    r"[:.]rand\.",
    r"UUID\.",
]

VOLATILE_PATTERN = re.compile("|".join(VOLATILE_INDICATORS))

def check(tool_name, params, targets):
    if not params:
        return None
        
    for content in _iter_candidate_content(tool_name, params):
        if not _is_liveview(content, targets):
            continue

        # Look inside mount functions only
        for mount_body in MOUNT_PATTERN.findall(content):
            for callback_body in ASSIGN_NEW_PATTERN.findall(mount_body):
                if VOLATILE_PATTERN.search(callback_body):
                    snippet = callback_body.strip()[:100]
                    return {
                        "reasoning": f"Detected volatile or query-backed callback in 'assign_new': {snippet}. Reconnects may cause stale data or performance issues due to doubled execution.",
                        "correction": "Prefer session handoff, parent-assign propagation, explicit 'assign/3' inside 'if connected?(socket)', or 'assign_async' for data loading"
                    }

    return None
