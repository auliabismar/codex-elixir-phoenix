"""
plan_aggregator.py — Aggregation layer for parallel sub-agent discovery outputs.

Merges XML-formatted discovery outputs from 4 parallel research agents into
a single unified prompt for plan generation. Handles conflict resolution
for overlapping information.
"""

import re
import xml.sax.saxutils as saxutils
from dataclasses import dataclass
from typing import Optional


@dataclass
class DiscoveryResult:
    role: str
    content: str
    xml_block: str


class PlanAggregator:
    ROLES = [
        "ecto-schema-analyzer",
        "phoenix-router-mapper",
        "liveview-component-scanner",
        "dependency-auditor",
    ]

    def __init__(self):
        self.discoveries: list[DiscoveryResult] = []

    def add_discovery(self, role: str, content: str) -> None:
        # Resolve injection risk by escaping raw LLM content
        safe_content = saxutils.escape(content or "")
        xml_block = f'<discovery role="{role}">\n{safe_content}\n</discovery>'
        self.discoveries.append(DiscoveryResult(role=role, content=content, xml_block=xml_block))

    def _extract_overlaps(self) -> dict[str, list[str]]:
        overlaps = {}
        
        # Enhanced regex to capture Elixir route-to-component mappings more accurately
        route_pattern = re.compile(r'(?:route|path|scope|get|post)\s*[=:(]?\s*["\']?([^"\'\n\s>]+)', re.IGNORECASE)
        component_pattern = re.compile(r'(?:liveview|LiveView|component|module)\s*[=:(]?\s*["\']?([^"\'\n\s>]+)', re.IGNORECASE)

        router_content = ""
        liveview_content = ""

        # Safe role matching with dash-to-underscore normalization
        for d in self.discoveries:
            role_norm = d.role.replace('_', '-')
            if role_norm == "phoenix-router-mapper":
                router_content = d.content
            elif role_norm == "liveview-component-scanner":
                liveview_content = d.content

        if not router_content or not liveview_content:
            return overlaps

        router_routes = set(route_pattern.findall(router_content))
        liveview_components = set(component_pattern.findall(liveview_content))

        # Filter out very short strings to avoid false positives in overlap matching
        router_routes = {r for r in router_routes if len(r) > 2}
        liveview_components = {c for c in liveview_components if len(c) > 2}

        for route in sorted(router_routes):
            # Strip common suffixes and slashes for better matching
            route_base = route.lower().replace('_path', '').replace('_url', '').strip('/')
            
            for component in sorted(liveview_components):
                comp_base = component.lower().replace('live', '').replace('component', '').replace('view', '')
                
                # Heuristic mapping: if the bases share a significant slug
                if route_base and comp_base and (route_base in comp_base or comp_base in route_base):
                    if route not in overlaps:
                        overlaps[route] = []
                    overlaps[route].append(component)

        return overlaps

    def resolve_conflicts(self) -> list[str]:
        conflicts = self._extract_overlaps()
        resolutions = []
        
        for route, components in conflicts.items():
            if len(components) > 1:
                resolutions.append(f"Route '{route}' mapped to multiple components: {', '.join(components)}. Prioritizing first discovery.")
        
        return resolutions

    def aggregate(self) -> str:
        # Ensure all expected roles are accounted for
        observed_roles = {d.role.replace('_', '-') for d in self.discoveries}
        missing_roles = set(self.ROLES) - observed_roles
        
        for role in missing_roles:
            self.add_discovery(role, "ERROR: Discovery agent failed to return results or timed out.")

        blocks = [d.xml_block for d in self.discoveries]
        aggregated = "\n\n".join(blocks)

        resolutions = self.resolve_conflicts()
        if resolutions:
            conflict_section = "\n\n<!--\nConflict Resolutions:\n" + "\n".join(f"- {r}" for r in resolutions) + "\n-->"
            aggregated += conflict_section

        return aggregated

    def get_role_content(self, role: str) -> Optional[str]:
        role_norm = role.replace('_', '-')
        for d in self.discoveries:
            if d.role.replace('_', '-') == role_norm:
                return d.content
        return None


def aggregate_discovery_outputs(outputs: dict[str, str]) -> str:
    aggregator = PlanAggregator()
    
    for role, content in outputs.items():
        aggregator.add_discovery(role, content)
    
    return aggregator.aggregate()


def parse_discovery_xml(xml_string: str) -> dict[str, str]:
    results = {}
    
    # Non-greedy matching for safety across discovery blocks
    pattern = re.compile(r'<discovery role="([^"]+)">\s*(.*?)\s*</discovery>', re.DOTALL)
    for match in pattern.finditer(xml_string):
        role = match.group(1)
        content = match.group(2).strip()
        # Unescape during parsing
        results[role] = saxutils.unescape(content)
    
    return results
