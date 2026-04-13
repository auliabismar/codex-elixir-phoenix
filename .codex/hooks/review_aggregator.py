"""
review_aggregator.py -- Deterministic synthesis for parallel $phx-review outputs.

Consumes structured reviewer payloads, backfills missing/timeout reviewers,
deduplicates overlaps, and emits a stable prioritized checklist.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET


_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_DEFAULT_SEVERITY = "medium"


@dataclass(frozen=True)
class ReviewFinding:
    role: str
    severity: str
    title: str
    detail: str
    file: str
    recommendation: str


@dataclass(frozen=True)
class ReviewParseResult:
    findings: list[ReviewFinding]
    unavailable: bool


class ReviewAggregator:
    """Collects reviewer outputs and produces a deterministic checklist."""

    ROLES = ["idiom", "security", "performance", "architecture"]

    def __init__(self, expected_roles: Sequence[str] | None = None):
        self.expected_roles = list(expected_roles or self.ROLES)
        self.outputs: dict[str, str] = {}

    def add_output(self, role: str, content: str) -> None:
        self.outputs[role.strip().lower()] = content or ""

    def aggregate(self) -> dict[str, object]:
        findings: list[ReviewFinding] = []
        missing_roles: list[str] = []

        for role in self.expected_roles:
            content = self.outputs.get(role)
            if content is None:
                findings.append(_build_unavailable_finding(role, "missing"))
                missing_roles.append(role)
                continue

            parsed = _parse_review_output(role, content)
            if parsed.unavailable:
                findings.append(_build_unavailable_finding(role, "timeout"))
                missing_roles.append(role)
                continue

            findings.extend(parsed.findings)

        for role, content in sorted(self.outputs.items()):
            if role in self.expected_roles:
                continue
            parsed = _parse_review_output(role, content)
            if parsed.unavailable:
                findings.append(_build_unavailable_finding(role, "timeout"))
                missing_roles.append(role)
            else:
                findings.extend(parsed.findings)

        checklist = _dedupe_and_sort(findings)
        return {
            "checklist": checklist,
            "missing_reviewers": sorted(set(missing_roles)),
            "total_findings": len(checklist),
        }


def aggregate_review_outputs(outputs: Mapping[str, str]) -> dict[str, object]:
    aggregator = ReviewAggregator()
    for role, content in outputs.items():
        aggregator.add_output(role, content)
    return aggregator.aggregate()


def render_prioritized_checklist(summary: Mapping[str, object]) -> str:
    items = summary.get("checklist") or []
    lines = ["Prioritized Refactoring Checklist"]
    if not items:
        lines.append("- No findings reported.")
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        reviewers = ", ".join(item["reviewers"])  # type: ignore[index]
        file_suffix = f" ({item['file']})" if item["file"] else ""  # type: ignore[index]
        lines.append(
            f"{index}. [{str(item['severity']).upper()}] {item['title']}{file_suffix} -- "
            f"reviewers: {reviewers}"
        )
        if item["recommendation"]:  # type: ignore[index]
            lines.append(f"   action: {item['recommendation']}")
    return "\n".join(lines)


def _parse_review_output(role: str, content: str) -> ReviewParseResult:
    text = (content or "").strip()
    if not text:
        return ReviewParseResult(findings=[], unavailable=True)

    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        if _looks_unavailable_text(text):
            return ReviewParseResult(findings=[], unavailable=True)
        return ReviewParseResult(
            findings=[
                ReviewFinding(
                    role=role,
                    severity=_DEFAULT_SEVERITY,
                    title=f"Unstructured finding from {role}",
                    detail=text,
                    file="",
                    recommendation="Return structured <review> output for deterministic synthesis.",
                )
            ],
            unavailable=False,
        )

    if root.tag != "review":
        if _looks_unavailable_text(text):
            return ReviewParseResult(findings=[], unavailable=True)
        return ReviewParseResult(
            findings=[
                ReviewFinding(
                    role=role,
                    severity=_DEFAULT_SEVERITY,
                    title=f"Unexpected review payload from {role}",
                    detail=text,
                    file="",
                    recommendation="Return <review> root with <finding> entries.",
                )
            ],
            unavailable=False,
        )

    status = (root.findtext("status") or "").strip().lower()
    if status in {"timeout", "timed-out", "unavailable", "failed"}:
        return ReviewParseResult(findings=[], unavailable=True)

    findings: list[ReviewFinding] = []
    for node in root.findall("finding"):
        title = (node.findtext("title") or "").strip()
        detail = (node.findtext("detail") or node.findtext("description") or "").strip()
        file = (node.findtext("file") or "").strip()
        recommendation = (
            node.findtext("recommendation")
            or node.findtext("action")
            or ""
        ).strip()
        severity = _normalize_severity(
            (node.attrib.get("severity") or node.findtext("severity") or "").strip()
        )

        if not title:
            title = detail or f"Finding from {role}"

        findings.append(
            ReviewFinding(
                role=role,
                severity=severity,
                title=title,
                detail=detail,
                file=file,
                recommendation=recommendation,
            )
        )

    if not findings:
        nested_result = _parse_nested_review(role, root)
        if nested_result is not None:
            return nested_result
        if _looks_unavailable_text(text):
            return ReviewParseResult(findings=[], unavailable=True)
        return ReviewParseResult(findings=[], unavailable=False)

    return ReviewParseResult(findings=findings, unavailable=False)


def _parse_nested_review(role: str, root: ET.Element) -> ReviewParseResult | None:
    nested_findings: list[ReviewFinding] = []
    saw_nested_review = False
    saw_unavailable = False

    for child in root:
        if child.tag != "review":
            continue

        saw_nested_review = True
        nested_payload = ET.tostring(child, encoding="unicode")
        parsed = _parse_review_output(role, nested_payload)
        if parsed.unavailable:
            saw_unavailable = True
            continue
        nested_findings.extend(parsed.findings)

    if nested_findings:
        return ReviewParseResult(findings=nested_findings, unavailable=False)
    if saw_nested_review and saw_unavailable:
        return ReviewParseResult(findings=[], unavailable=True)
    if saw_nested_review:
        return ReviewParseResult(findings=[], unavailable=False)
    return None


def _build_unavailable_finding(role: str, reason: str) -> ReviewFinding:
    if reason == "missing":
        detail = "No reviewer output was received for this role."
    else:
        detail = "Reviewer timed out or returned an unavailable status."
    return ReviewFinding(
        role=role,
        severity="medium",
        title=f"Reviewer unavailable: {role}",
        detail=detail,
        file="",
        recommendation="Re-run $phx-review for full 4-domain coverage.",
    )


def _normalize_severity(value: str) -> str:
    severity = value.strip().lower()
    return severity if severity in _SEVERITY_ORDER else _DEFAULT_SEVERITY


def _dedupe_and_sort(findings: Sequence[ReviewFinding]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}

    for finding in findings:
        key = _dedupe_key(finding)
        existing = merged.get(key)
        if existing is None:
            merged[key] = {
                "severity": finding.severity,
                "title": finding.title,
                "detail": finding.detail,
                "file": finding.file,
                "recommendation": finding.recommendation,
                "reviewers": {finding.role},
            }
            continue

        if _SEVERITY_ORDER[finding.severity] < _SEVERITY_ORDER[str(existing["severity"])]:
            existing["severity"] = finding.severity

        if finding.detail and not existing["detail"]:
            existing["detail"] = finding.detail
        if finding.file and not existing["file"]:
            existing["file"] = finding.file
        if finding.recommendation and not existing["recommendation"]:
            existing["recommendation"] = finding.recommendation
        existing["reviewers"].add(finding.role)  # type: ignore[union-attr]

    checklist = []
    for item in merged.values():
        reviewers = sorted(item["reviewers"])  # type: ignore[arg-type]
        checklist.append({**item, "reviewers": reviewers})

    checklist.sort(
        key=lambda item: (
            _SEVERITY_ORDER[str(item["severity"])],
            str(item["title"]).lower(),
            str(item["file"]).lower(),
        )
    )
    return checklist


def _dedupe_key(finding: ReviewFinding) -> str:
    parts = [finding.title, finding.detail, finding.file]
    return "|".join(_normalize_text(part) for part in parts)


def _normalize_text(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip().lower())
    return collapsed


def _looks_unavailable_text(content: str) -> bool:
    normalized = content.strip().lower()
    return any(
        marker in normalized
        for marker in (
            "timeout",
            "timed out",
            "unavailable",
            "failed to return",
            "error: discovery agent failed",
        )
    )
