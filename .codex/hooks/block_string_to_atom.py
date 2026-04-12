import re

# Story 4.2: Built-In Data Type Protection Patterns - Dynamic Atom Protection
# Contract: check(tool_name: str, params: dict, targets: list[str]) -> dict | None

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

# Matches String.to_atom( ... )
STRING_TO_ATOM_PATTERN = re.compile(r"String\.to_atom\s*\((.*?)\)", re.DOTALL)


def _iter_added_patch_lines(patch_text):
    for line in patch_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            yield line[1:]


def _iter_candidate_content(tool_name, params):
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


def _is_safe_literal(argument):
    return (
        argument.startswith('"') and argument.endswith('"') and "#{" not in argument
    ) or (
        argument.startswith("'") and argument.endswith("'") and "#{" not in argument
    )


def check(tool_name, params, targets):
    """
    Inspects pending write payloads for unsafe String.to_atom usage.
    """
    for content in _iter_candidate_content(tool_name, params):
        matches = STRING_TO_ATOM_PATTERN.findall(content)
        for arg in matches:
            normalized_arg = arg.strip()
            if not _is_safe_literal(normalized_arg):
                return {
                    "reasoning": f"Unsafe dynamic atom creation detected in 'String.to_atom({normalized_arg})' which can lead to memory exhaustion",
                    "correction": "Use String.to_existing_atom/1 or an explicit allowlist mapping to safe atoms",
                }

    return None
