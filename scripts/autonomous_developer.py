"""Create a reviewable developer queue from canonical cycle proposals.

The agent is intentionally proposal-first: it may prepare documentation and
quality-work artifacts, but it never edits production code or merges a change.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_REPORTS = 100
MAX_PROPOSALS = 50


def _safe(value: Any, limit: int = 500) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def collect(root: Path) -> list[dict[str, str]]:
    proposals: list[dict[str, str]] = []
    reports = sorted((root / "reports").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for report_path in reports[:MAX_REPORTS]:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        governance = report.get("governance") if isinstance(report, dict) else {}
        candidates = governance.get("open_proposals", []) if isinstance(governance, dict) else []
        if not isinstance(candidates, list):
            continue
        for item in candidates:
            if not isinstance(item, dict):
                continue
            proposals.append({
                "title": _safe(item.get("title", "Untitled proposal"), 180),
                "rationale": _safe(item.get("rationale", item.get("reason", ""))),
                "impact": _safe(item.get("impact_area", item.get("area", "quality")), 120),
                "source": report_path.name,
            })
            if len(proposals) >= MAX_PROPOSALS:
                return proposals
    return proposals


def render(proposals: list[dict[str, str]]) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Autonomous Developer Queue",
        "",
        f"Generated at `{now}`.",
        "",
        "> This is a review queue, not an authorization to change production code. Every implementation must pass CI and receive human review through a pull request.",
        "",
    ]
    if not proposals:
        lines.append("No new reviewable proposals were found.")
        return "\n".join(lines) + "\n"
    lines.extend(["| Priority | Proposal | Impact | Source |", "|---:|---|---|---|"])
    for index, proposal in enumerate(proposals, start=1):
        title = proposal["title"].replace("|", "-")
        impact = proposal["impact"].replace("|", "-")
        source = proposal["source"].replace("|", "-")
        lines.append(f"| {index} | {title} | {impact} | `{source}` |")
        if proposal["rationale"]:
            lines.append(f"|  | Rationale: {proposal['rationale'].replace('|', '-') } |  |  |")
    lines.extend([
        "",
        "## Required review gates",
        "",
        "1. Confirm the proposal is within peaceful civilian-energy scope.",
        "2. Add or update deterministic tests before implementation.",
        "3. Run safety, health, compile and regression checks.",
        "4. Require human approval before merge or any external write.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = Path(os.getenv("NI_PROJECT_ROOT", Path.cwd())).resolve()
    output = root / "reports" / "developer_queue.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(collect(root)), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
