# Shared utilities for Iron Law hooks (Epic 4 Action Item)
import re

# Detection Patterns
USE_LIVE_VIEW_PATTERN = re.compile(
    r"use\s+([a-zA-Z0-9_.]+(?:Web)?\s*,\s*:live_view|Phoenix\.LiveView)",
    re.MULTILINE
)

LIVEVIEW_PATH_INDICATORS = {
    "_live.ex",
    "/live/",
    "\\live\\",
}

# Parameter Mapping
DIRECT_CONTENT_KEYS = (
    "CodeContent",
    "ReplacementContent",
    "TargetContent",
    "content",
    "input",
    "new_content",
    "new_str",
    "replacement",
)
PATCH_CONTENT_KEYS = ("input", "patch", "content")

def is_liveview(content: str, target_files: list[str] = None) -> bool:
    """Detect if content or target files represent a Phoenix LiveView."""
    if target_files:
        for target in target_files:
            if any(ind in target for ind in LIVEVIEW_PATH_INDICATORS):
                return True
    
    return bool(USE_LIVE_VIEW_PATTERN.search(content))

def is_oban_worker(content: str) -> bool:
    """Detect if content represents an Oban worker."""
    return bool(re.search(r"use\s+Oban\.Worker", content))

def iter_added_patch_lines(patch_text: str):
    """Iterate over lines added in a unified diff patch."""
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            yield line[1:]

def iter_candidate_content(tool_name: str, params: dict):
    """
    Generator that yields relevant content from tool parameters.
    Handles both direct writes and added lines from patches.
    """
    if not params:
        return

    if tool_name == "apply_patch":
        for key in PATCH_CONTENT_KEYS:
            value = params.get(key)
            if isinstance(value, str) and value.strip():
                added_lines = "\n".join(iter_added_patch_lines(value)).strip()
                if added_lines:
                    yield added_lines
        return

    for key in DIRECT_CONTENT_KEYS:
        value = params.get(key)
        if isinstance(value, str) and value.strip():
            yield value

def extract_content(params: dict, tool_name: str = "write_to_file") -> str:
    """Extract first available content chunk (Legacy helper for simple hooks)."""
    for content in iter_candidate_content(tool_name, params):
        return content
    return ""
