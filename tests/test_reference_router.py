"""
Tests for .codex/hooks/reference_router.py.
"""

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).parent.parent / ".codex" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from reference_router import ReferenceRouter, format_reference_block  # noqa: E402


def write_reference(root: Path, relative_path: str, content: str) -> None:
    path = root / ".codex" / "references" / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_config(root: Path, payload: dict | str) -> None:
    config_path = root / ".codex" / "references" / "routing.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        config_path.write_text(payload, encoding="utf-8")
        return
    config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_invalid_config_falls_back_to_core_references(tmp_path):
    repo_root = tmp_path / "repo"
    write_reference(repo_root, "elixir-basics.md", "# Elixir Basics")
    write_reference(repo_root, "code-organization.md", "# Code Organization")
    write_config(repo_root, "{invalid json")

    refs = ReferenceRouter(repo_root).find_references("create user schema", max_refs=3)

    assert [ref["domain"] for ref in refs] == ["core", "core"]
    assert [ref["name"] for ref in refs] == ["elixir-basics", "code-organization"]


def test_keyword_matching_uses_word_boundaries(tmp_path):
    repo_root = tmp_path / "repo"
    write_reference(repo_root, "api/api-view.md", "# API View")
    write_reference(repo_root, "elixir-basics.md", "# Elixir Basics")
    write_reference(repo_root, "code-organization.md", "# Code Organization")
    write_config(
        repo_root,
        {
            "routes": [
                {
                    "keywords": ["view"],
                    "domain": "api",
                    "references": ["api-view.md"],
                }
            ],
            "fallback": {
                "references": ["elixir-basics.md", "code-organization.md"],
            },
        },
    )

    refs = ReferenceRouter(repo_root).find_references("preview dashboard", max_refs=2)

    assert [ref["domain"] for ref in refs] == ["core", "core"]


def test_balances_references_across_matched_domains(tmp_path):
    repo_root = tmp_path / "repo"
    write_reference(repo_root, "ecto/ecto-schema-basics.md", "# Schema")
    write_reference(repo_root, "ecto/ecto-changesets.md", "# Changesets")
    write_reference(repo_root, "testing/testing-basics.md", "# Testing Basics")
    write_reference(repo_root, "testing/testing-data-case.md", "# Data Case")
    write_reference(repo_root, "elixir-basics.md", "# Elixir Basics")
    write_reference(repo_root, "code-organization.md", "# Code Organization")
    write_config(
        repo_root,
        {
            "routes": [
                {
                    "keywords": ["schema"],
                    "domain": "ecto",
                    "references": ["ecto-schema-basics.md", "ecto-changesets.md"],
                },
                {
                    "keywords": ["test"],
                    "domain": "testing",
                    "references": ["testing-basics.md", "testing-data-case.md"],
                },
            ],
            "fallback": {
                "references": ["elixir-basics.md", "code-organization.md"],
            },
        },
    )

    refs = ReferenceRouter(repo_root).find_references("add schema test coverage", max_refs=3)

    assert [ref["domain"] for ref in refs] == ["ecto", "testing", "ecto"]
    assert [ref["name"] for ref in refs] == [
        "ecto-schema-basics",
        "testing-basics",
        "ecto-changesets",
    ]


def test_missing_route_files_fall_back_to_core_references(tmp_path):
    repo_root = tmp_path / "repo"
    write_reference(repo_root, "elixir-basics.md", "# Elixir Basics")
    write_reference(repo_root, "code-organization.md", "# Code Organization")
    write_config(
        repo_root,
        {
            "routes": [
                {
                    "keywords": ["schema"],
                    "domain": "ecto",
                    "references": ["missing.md"],
                }
            ],
            "fallback": {
                "references": ["elixir-basics.md", "code-organization.md"],
            },
        },
    )

    refs = ReferenceRouter(repo_root).find_references("schema update", max_refs=2)

    assert [ref["domain"] for ref in refs] == ["core", "core"]


def test_reference_block_uses_cdata_wrapping(tmp_path):
    repo_root = tmp_path / "repo"
    write_reference(repo_root, "elixir-basics.md", "Use <tag> && keep ]]> safe.")
    write_reference(repo_root, "code-organization.md", "# Code Organization")
    write_config(
        repo_root,
        {
            "routes": [],
            "fallback": {
                "references": ["elixir-basics.md"],
            },
        },
    )

    block = format_reference_block(repo_root, "no matching route", max_refs=1)

    assert "<![CDATA[" in block
    assert "Use <tag> && keep ]]]]><![CDATA[> safe." in block


def test_repository_routing_config_points_only_to_existing_files():
    repo_root = Path(__file__).resolve().parent.parent
    references_dir = repo_root / ".codex" / "references"
    routing = json.loads((references_dir / "routing.json").read_text(encoding="utf-8"))

    missing = []
    for route in routing.get("routes", []):
        domain = route["domain"]
        for ref_name in route.get("references", []):
            if not (references_dir / domain / ref_name).exists():
                missing.append(f"{domain}/{ref_name}")

    for ref_name in routing.get("fallback", {}).get("references", []):
        if not (references_dir / ref_name).exists():
            missing.append(ref_name)

    assert missing == []


def test_repository_routing_surfaces_introspection_playbook_for_state_debugging_tasks():
    repo_root = Path(__file__).resolve().parent.parent

    refs = ReferenceRouter(repo_root).find_references(
        "investigate GenServer timeout in handle_call",
        max_refs=3,
    )

    assert any(
        ref["domain"] == "introspection" and ref["name"] == "tidewave-playbook"
        for ref in refs
    )
