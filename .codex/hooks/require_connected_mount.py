import re
import iron_law_utils

# Story 4.3: Phoenix LiveView Architectural Guardrails - connected? mount enforcement
# Refactored to use iron_law_utils (Epic 4 Action Item)

# Use a safer regex for mount extraction
MOUNT_PATTERN = re.compile(
    r"def\s+mount\s*\(\s*[^,]*\s*,\s*[^,]*\s*,\s*([a-zA-Z0-9_]+)\s*\)\s*do\b(.*?)(?=\ndef\s|$)",
    re.DOTALL
)

# Query/Subscription indicators
QUERY_INDICATORS = [
    r"Repo\.",
    r"PubSub\.subscribe",
    r"\b[A-Z][a-zA-Z0-9_]*\.(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
    r"\b(list|search|paginate|load|fetch|get)_[a-zA-Z0-9_]+",
]

QUERY_PATTERN = re.compile("|".join(QUERY_INDICATORS))

def _has_connected_guard(body, socket_name):
    guard_pattern = re.compile(rf"(if\s+connected\?\(\s*{socket_name}\s*\)|{socket_name}\s*\|>\s*connected\?\(\s*\))")
    return bool(guard_pattern.search(body))

def check(tool_name: str, params: dict, targets: list[str]) -> dict | None:
    for content in iron_law_utils.iter_candidate_content(tool_name, params):
        if not iron_law_utils.is_liveview(content, targets):
            continue

        for socket_name, body in MOUNT_PATTERN.findall(content):
            if QUERY_PATTERN.search(body) and not _has_connected_guard(body, socket_name):
                return {
                    "reasoning": f"Detected data fetching or subscription in 'mount/3' using socket '{socket_name}' without a 'connected?' guard. This will double-run on every connection.",
                    "correction": f"Wrap database queries and PubSub subscriptions in 'if connected?({socket_name}) do ... end', or use 'assign_async' to defer loading"
                }

    return None
