"""
reference_router.py — Contextual routing for domain reference documents.

Maps task keywords/zones to relevant reference files for specialist agents.
"""

from __future__ import annotations

import json
import re
from json import JSONDecodeError
from pathlib import Path

DEFAULT_FALLBACK_REFERENCES = ("elixir-basics.md", "code-organization.md")
SCRIPT_REPO_ROOT = Path(__file__).resolve().parents[2]


class ReferenceRouter:
    """Routes task context to relevant domain reference documents."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.ref_dir = self.repo_root / ".codex" / "references"
        self.routing_config = self._load_routing_config()

    def _default_config(self) -> dict:
        return {
            "routes": [],
            "fallback": {"references": list(DEFAULT_FALLBACK_REFERENCES)},
        }

    def _load_routing_config(self) -> dict:
        """Load the routing configuration from routing.json."""
        config_path = self.ref_dir / "routing.json"
        if not config_path.exists():
            return self._default_config()

        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except JSONDecodeError:
            return self._default_config()

        if not isinstance(payload, dict):
            return self._default_config()

        payload.setdefault("routes", [])
        payload.setdefault(
            "fallback",
            {"references": list(DEFAULT_FALLBACK_REFERENCES)},
        )
        return payload

    def find_references(self, task_text: str, max_refs: int = 5) -> list[dict]:
        """
        Find relevant reference documents based on task text.

        Args:
            task_text: The task description or checklist item
            max_refs: Maximum number of references to return

        Returns:
            List of reference dictionaries with 'name', 'path', 'content'
        """
        if max_refs <= 0:
            return []

        task_lower = task_text.lower()
        seen_paths: set[Path] = set()
        matched_groups: list[list[dict]] = []

        for route in self.routing_config.get("routes", []):
            if not self._route_matches(task_lower, route):
                continue

            group = self._resolve_reference_group(route, seen_paths)
            if group:
                matched_groups.append(group)

        if matched_groups:
            return self._round_robin_select(matched_groups, max_refs)

        return self._fallback_references(max_refs, seen_paths)

    def get_reference_block(self, task_text: str, max_refs: int = 5) -> str:
        """
        Generate a reference block for injection into agent context.

        Returns a formatted string with <reference> XML tags.
        """
        refs = self.find_references(task_text, max_refs)
        return self.render_reference_block(refs)

    def render_reference_block(self, refs: list[dict]) -> str:
        if not refs:
            return ""

        lines = ["", "<!-- INJECTED REFERENCES -->"]
        for ref in refs:
            safe_content = self._wrap_cdata(ref["content"])
            lines.extend(
                [
                    f'<reference name="{ref["name"]}" domain="{ref["domain"]}">',
                    "<![CDATA[",
                    safe_content,
                    "]]>",
                    "</reference>",
                ]
            )
        return "\n".join(lines) + "\n"

    def _route_matches(self, task_lower: str, route: dict) -> bool:
        keywords = route.get("keywords", [])
        return any(
            self._keyword_matches(task_lower, keyword)
            for keyword in keywords
            if isinstance(keyword, str)
        )

    @staticmethod
    def _keyword_matches(task_lower: str, keyword: str) -> bool:
        token = keyword.strip().lower()
        if not token:
            return False

        pattern = rf"(?<![a-z0-9_]){re.escape(token)}(?![a-z0-9_])"
        return re.search(pattern, task_lower) is not None

    def _resolve_reference_group(self, route: dict, seen_paths: set[Path]) -> list[dict]:
        domain = route.get("domain", "core")
        refs: list[dict] = []

        for ref_file in route.get("references", []):
            ref_path = self.ref_dir / domain / ref_file
            loaded = self._load_reference(ref_path, domain, ref_file, seen_paths)
            if loaded:
                refs.append(loaded)

        return refs

    def _fallback_references(self, max_refs: int, seen_paths: set[Path]) -> list[dict]:
        fallback = self.routing_config.get("fallback", {})
        refs: list[dict] = []

        for ref_file in fallback.get("references", DEFAULT_FALLBACK_REFERENCES):
            ref_path = self.ref_dir / ref_file
            loaded = self._load_reference(ref_path, "core", ref_file, seen_paths)
            if loaded:
                refs.append(loaded)
            if len(refs) >= max_refs:
                break

        return refs

    def _load_reference(
        self,
        ref_path: Path,
        domain: str,
        ref_file: str,
        seen_paths: set[Path],
    ) -> dict | None:
        if not ref_path.exists():
            return None

        resolved = ref_path.resolve()
        if resolved in seen_paths:
            return None
        seen_paths.add(resolved)

        return {
            "name": ref_file.removesuffix(".md"),
            "domain": domain,
            "path": str(resolved),
            "content": resolved.read_text(encoding="utf-8"),
        }

    @staticmethod
    def _round_robin_select(groups: list[list[dict]], max_refs: int) -> list[dict]:
        selected: list[dict] = []

        while len(selected) < max_refs and any(groups):
            for group in groups:
                if not group or len(selected) >= max_refs:
                    continue
                selected.append(group.pop(0))

        return selected

    @staticmethod
    def _wrap_cdata(content: str) -> str:
        return content.replace("]]>", "]]]]><![CDATA[>")


def build_reference_context(
    repo_root: str | Path,
    task_text: str,
    max_refs: int = 5,
) -> dict:
    """Return both the selected references and the formatted block."""
    router = ReferenceRouter(repo_root)
    refs = router.find_references(task_text, max_refs)
    return {
        "references": refs,
        "reference_block": router.render_reference_block(refs),
    }


def resolve_references(repo_root: str | Path, task_text: str, max_refs: int = 5) -> list[dict]:
    """Convenience function to resolve references for a task."""
    return build_reference_context(repo_root, task_text, max_refs)["references"]


def format_reference_block(repo_root: str | Path, task_text: str, max_refs: int = 5) -> str:
    """Convenience function to format reference block for agent context."""
    return build_reference_context(repo_root, task_text, max_refs)["reference_block"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        result = format_reference_block(SCRIPT_REPO_ROOT, task)
        print(result)
    else:
        print("Usage: python reference_router.py <task text>")
