import re

# Story 4.2: Built-In Data Type Protection Patterns - Money Detection
# Contract: check(tool_name: str, params: dict, targets: list[str]) -> dict | None

MONEY_FIELD_TOKENS = {
    "amount",
    "balance",
    "cost",
    "fee",
    "fees",
    "price",
    "subtotal",
    "total",
}
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

# Matches schema and migration DSL forms such as:
#   field :price, :float
#   field(:price, :float)
#   add :price, :float
#   modify :price, :float
# Matches schema and migration DSL forms - handles comments and multiline
FLOAT_FIELD_PATTERN = re.compile(
    r"(?:field|add|modify)\s*\(?\s*:([a-zA-Z0-9_]+)\s*,\s*(?:#.*?\n\s*)*:float\b",
    re.MULTILINE
)


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


def _is_money_field(field_name):
    tokens = {token for token in field_name.lower().split("_") if token}
    return bool(tokens & MONEY_FIELD_TOKENS)


def check(tool_name, params, targets):
    """
    Inspects pending write payloads for :float usage on money-like fields.
    """
    for content in _iter_candidate_content(tool_name, params):
        matches = FLOAT_FIELD_PATTERN.findall(content)
        for field_name in matches:
            if _is_money_field(field_name):
                return {
                    "reasoning": f"Detected :float usage for monetary field '{field_name}' which leads to rounding errors",
                    "correction": "Use :decimal (with the Decimal library) or :integer (representing cents) for monetary values",
                }

    return None
