import re
import iron_law_utils

# Story 4.3: Phoenix LiveView Architectural Guardrails - assign_new protection
# Refactored to use iron_law_utils (Epic 4 Action Item)

# Simplified match that finds assign_new calls inside mount functions
MOUNT_PATTERN = re.compile(
    r"def\s+mount\b.*?\bdo\b(.*?)(?=\ndef\s|$)",
    re.DOTALL
)

# Robust assign_new pattern: captures the function reference or tuple
ASSIGN_NEW_PATTERN = re.compile(
    r"assign_new\s*\([^,]+,\s*:[a-zA-Z0-9_]+\s*,\s*(fn\b.*?->.*?end|&[a-zA-Z0-9_./]+|\{[A-Z][a-zA-Z0-9_.]*,\s*:[a-zA-Z0-9_]+\s*,\s*\[.*?\]\})",
    re.DOTALL
)

# Volatile indicators
VOLATILE_INDICATORS = [
    r"Repo\.",
    r"\b[A-Z][a-zA-Z0-9_]*\.(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
    r"\b(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
    r"DateTime\.",
    r"Time\.",
    r"[:.]rand\.",
    r"UUID\.",
    r"Enum\.(random|take_random|shuffle)",
]

VOLATILE_PATTERN = re.compile("|".join(VOLATILE_INDICATORS))

def check(tool_name: str, params: dict, targets: list[str]) -> dict | None:
    for content in iron_law_utils.iter_candidate_content(tool_name, params):
        if not iron_law_utils.is_liveview(content, targets):
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
