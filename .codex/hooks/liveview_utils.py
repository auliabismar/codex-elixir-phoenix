import re

LIVEVIEW_INDICATORS = {
    "_live.ex",
    "/live/",
    "\\live\\",
}

USE_LIVE_VIEW_PATTERN = re.compile(
    r"use\s+([a-zA-Z0-9_.]+(?:Web)?\s*,\s*:live_view|Phoenix\.LiveView)",
    re.MULTILINE
)

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

def _iter_added_patch_lines(patch_text):
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            yield line[1:]

def _iter_candidate_content(tool_name, params):
    if not params:
        return
    if tool_name == "apply_patch":
        for key in PATCH_CONTENT_KEYS:
            value = params.get(key)
            if isinstance(value, str) and value:
                added_lines = "\n".join(_iter_added_patch_lines(value)).strip()
                if added_lines:
                    yield added_lines
        return

    for key in DIRECT_CONTENT_KEYS:
        value = params.get(key)
        if isinstance(value, str) and value:
            yield value

def _is_liveview(content, targets):
    if not targets:
        targets = []
    # Check by path
    for target in targets:
        if any(ind in target for ind in LIVEVIEW_INDICATORS):
            return True
    
    # Check by content
    if USE_LIVE_VIEW_PATTERN.search(content):
        return True
    
    return False
