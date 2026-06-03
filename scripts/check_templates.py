#!/usr/bin/env python3
"""Validate required Markdown templates exist and include key invariants."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_TEMPLATES = [
    "00_owner_intent.md",
    "01_case_intake.md",
    "02_team_selection.md",
    "02b_mode_selection.md",
    "03_debate_session.md",
    "04_team_verdict_block.md",
    "05_court_summary.md",
    "06_critical_assumption_check.md",
    "07_orchestrator_decision.md",
    "08_phase_plan.md",
    "09_executor_instruction.md",
    "10_execution_feedback.md",
    "11_acceptance_review.md",
    "12_lesson_proposal.md",
]

REQUIRED_SNIPPETS = {
    "01_case_intake.md": [
        "needs_execution:",
        "execution_authorized:",
        "authorized_phase:",
        "human_approval_required:",
        "court_verdict_tier:",
    ],
    "04_team_verdict_block.md": [
        "team_id:",
        "team_verdict_tier:",
        "Scores",
        "Assumptions",
        "Recommended next step",
    ],
    "07_orchestrator_decision.md": [
        "needs_execution:",
        "execution_authorized:",
        "authorized_phase:",
        "human_approval_required:",
    ],
    "09_executor_instruction.md": [
        "forbidden_actions",
        "验收标准",
        "停止并回报条件",
    ],
    "11_acceptance_review.md": [
        "Checklist",
        "未违反 forbidden_actions",
        "返工判定",
    ],
    "12_lesson_proposal.md": [
        "promote_to_lessons:",
        "promote_to_agents:",
        "promote_to_soul:",
        "失败/风险场景",
    ],
}


def check_templates(template_dir: Path) -> int:
    errors: list[str] = []

    for rel in REQUIRED_TEMPLATES:
        path = template_dir / rel
        if not path.is_file():
            errors.append(f"missing template: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in REQUIRED_SNIPPETS.get(rel, []):
            if snippet not in text:
                errors.append(f"{rel}: missing required snippet: {snippet}")

    print(f"templates_checked: {len(REQUIRED_TEMPLATES)}")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ERROR: {error}")
        print(f"\nResult: FAIL ({len(errors)} errors)")
        return 1
    print("\nResult: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown harness templates.")
    parser.add_argument("--template-dir", default="templates")
    args = parser.parse_args()
    return check_templates(Path(args.template_dir))


if __name__ == "__main__":
    raise SystemExit(main())
