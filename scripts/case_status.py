#!/usr/bin/env python3
"""Summarize a harness case's audit-chain progress and next action."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


BASE_CHAIN = [
    ("owner_intent", "00_owner_intent.md", "原始意图"),
    ("case_intake", "01_case_intake.md", "案件定义"),
    ("team_selection", "02_team_selection.md", "团队选择理由"),
    ("mode_selection", "02b_mode_selection.md", "模式选择理由"),
    ("debate_session", "03_debate_session.md", "辩论记录"),
    ("court_summary", "05_court_summary.md", "汇总 verdict"),
    ("cac", "06_critical_assumption_check.md", "关键前提检查"),
    ("decision", "07_orchestrator_decision.md", "Orchestrator 决策"),
    ("phase_plan", "08_phase_plan.md", "Phase 规划"),
    ("instruction", "09_executor_instruction.md", "执行任务书"),
    ("feedback", "10_execution_feedback.md", "执行反馈"),
    ("acceptance", "11_acceptance_review.md", "验收结果"),
    ("lesson", "12_lesson_proposal.md", "lesson proposal"),
]

RECOMMENDED_PLUS = {
    "RECOMMENDED_WITH_MODIFICATIONS",
    "RECOMMENDED",
    "IMMEDIATELY_RECOMMENDED",
}


def parse_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    data: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = parse_scalar(strip_inline_comment(value).strip())
    return data


def strip_inline_comment(value: str) -> str:
    in_quote: str | None = None
    for index, char in enumerate(value):
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        elif char == "#" and in_quote is None:
            return value[:index]
    return value


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "None", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def bool_value(value: Any) -> bool:
    return value is True


def required_chain(case_dir: Path, intake: dict[str, Any], decision: dict[str, Any]) -> list[tuple[str, str, str]]:
    chain = BASE_CHAIN.copy()
    needs_execution = bool_value(decision.get("needs_execution", intake.get("needs_execution")))
    authorized = bool_value(
        decision.get("execution_authorized", intake.get("execution_authorized"))
    )
    risk = intake.get("risk_tier")
    verdict = intake.get("court_verdict_tier")
    cac_required = risk in {"high", "critical"} or verdict in RECOMMENDED_PLUS

    if not cac_required:
        chain = [item for item in chain if item[0] != "cac"]
    if not needs_execution or not authorized:
        chain = [
            item
            for item in chain
            if item[0] not in {"phase_plan", "instruction", "feedback", "acceptance"}
        ]
    return chain


def next_action(missing: list[tuple[str, str, str]], intake: dict[str, Any], decision: dict[str, Any]) -> str:
    if not missing:
        return "运行 `python3 scripts/validate_case.py <case_dir>`；通过后可考虑 completed。"

    key = missing[0][0]
    if key == "team_selection":
        return "运行 `python3 scripts/suggest_teams.py <case_dir> --write`，再人工补充理由。"
    if key == "mode_selection":
        return "运行 `python3 scripts/suggest_modes.py <case_dir> --write`，再人工补充时间成本与模型分配。"
    if key == "instruction":
        authorized = bool_value(
            decision.get("execution_authorized", intake.get("execution_authorized"))
        )
        if not authorized:
            return "先在 `07_orchestrator_decision.md` 明确授权四字段，不要写可执行任务书。"
        return "填写 `09_executor_instruction.md`，确保包含禁止事项、验收标准、停止条件。"
    if key == "cac":
        return "填写 `06_critical_assumption_check.md`，列出事实/推断/未知与翻转条件。"
    return f"补齐 `{missing[0][1]}`。"


def summarize(case_dir: Path) -> int:
    if not case_dir.is_dir():
        print(f"ERROR: case directory does not exist: {case_dir}")
        return 1

    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    chain = required_chain(case_dir, intake, decision)
    missing = [item for item in chain if not (case_dir / item[1]).is_file()]
    present = [item for item in chain if (case_dir / item[1]).is_file()]

    print(f"case_dir: {case_dir}")
    print(f"case_id: {intake.get('case_id', '(unknown)')}")
    print(f"status: {intake.get('status', '(unknown)')}")
    print(f"case_type: {intake.get('case_type', '(unknown)')}")
    print(f"risk_tier: {intake.get('risk_tier', '(unknown)')}")
    print(f"needs_execution: {intake.get('needs_execution', '(unknown)')}")
    print(
        "execution_authorized: "
        f"{decision.get('execution_authorized', intake.get('execution_authorized', '(unknown)'))}"
    )
    print()

    print("present:")
    for _, rel, label in present:
        print(f"  OK   {rel} — {label}")

    print("\nmissing:")
    if missing:
        for _, rel, label in missing:
            print(f"  MISS {rel} — {label}")
    else:
        print("  none")

    print(f"\nnext_action: {next_action(missing, intake, decision)}")
    return 0 if not missing else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize harness case progress.")
    parser.add_argument("case_dir", help="Path to cases/.../CASE-... directory")
    args = parser.parse_args()
    return summarize(Path(args.case_dir))


if __name__ == "__main__":
    raise SystemExit(main())
