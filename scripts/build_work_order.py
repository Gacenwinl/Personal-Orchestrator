#!/usr/bin/env python3
"""Build a structured JSON work order from 09_executor_instruction.md.

Merges fields from 01_case_intake.md, 07_orchestrator_decision.md, and
05_court_summary.md into a single machine-readable work order following
templates/work_order_schema.yaml.

Usage:
    python3 scripts/build_work_order.py cases/active/CASE-xxx
    make work-order CASE=cases/active/CASE-xxx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    ROOT,
    parse_frontmatter,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$(.+?)(?=^##\s+|\Z)"
    match = re.search(pattern, body, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_bullets(text: str) -> list[str]:
    return [
        line[2:].strip()
        for line in text.splitlines()
        if line.strip().startswith("- ")
    ]


def read_body(path: Path) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)
    return text


def build_work_order(case_dir: Path) -> dict:
    case_dir = case_dir.resolve()

    intake_fm = parse_frontmatter(case_dir / "01_case_intake.md")
    decision_fm = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    instruction_fm = parse_frontmatter(case_dir / "09_executor_instruction.md")

    case_id = intake_fm.get("case_id", case_dir.name)
    phase = instruction_fm.get("phase", decision_fm.get("authorized_phase", "phase1"))
    today = date.today().strftime("%Y%m%d")
    task_id = f"{case_id}-{phase}-{today}"

    instruction_body = read_body(case_dir / "09_executor_instruction.md")
    court_body = read_body(case_dir / "05_court_summary.md")
    decision_body = read_body(case_dir / "07_orchestrator_decision.md")

    steps = extract_bullets(extract_section(instruction_body, "执行步骤"))
    forbidden = extract_bullets(extract_section(instruction_body, "禁止事项（forbidden_actions）"))
    acceptance_raw = extract_bullets(extract_section(instruction_body, "验收标准（Orchestrator 将据此填 11）"))
    failure_section = extract_section(instruction_body, "失败处理")
    outputs_section = extract_section(instruction_body, "输出文件")
    inputs_section = extract_section(instruction_body, "输入文件")

    # Upstream depends on: read bullet list from "输入文件"
    upstream = extract_bullets(inputs_section) if inputs_section else []

    # execution context: court summary + decision summary (first 2000 chars)
    context_parts = []
    if court_body:
        context_parts.append(f"[Court Summary]\n{court_body[:800]}")
    if decision_body:
        context_parts.append(f"[Orchestrator Decision]\n{decision_body[:600]}")
    execution_context = "\n\n".join(context_parts)[:2000]

    # output files: parse table from 输出文件 section
    output_files: list[dict] = []
    for line in outputs_section.splitlines():
        if line.strip().startswith("|") and "---" not in line and "路径" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0]:
                output_files.append({
                    "path": cells[0],
                    "format": cells[1] if len(cells) > 1 else "",
                    "required_fields": [cells[2]] if len(cells) > 2 and cells[2] else [],
                })

    # failure strategy: try to parse from 09 or use schema defaults
    failure_strategy = {
        "timeout_action": "stop and report to Orchestrator",
        "under_delivery_action": "partial output + gap log",
        "loop_threshold": 3,
        "loop_action": "stop + write daemon_error.log",
    }
    if "timeout" in failure_section.lower():
        for line in failure_section.splitlines():
            if "timeout" in line.lower() or "超时" in line:
                failure_strategy["timeout_action"] = line.strip("- ").strip()
            if "loop" in line.lower() or "循环" in line:
                failure_strategy["loop_action"] = line.strip("- ").strip()

    # rollback checkpoint: last present file in chain
    chain_files = [
        "09_executor_instruction.md",
        "07_orchestrator_decision.md",
        "05_court_summary.md",
        "03_debate_session.md",
        "01_case_intake.md",
    ]
    rollback_checkpoint = ""
    for f in chain_files:
        if (case_dir / f).is_file():
            rollback_checkpoint = f
            break

    # downstream gates: what depends on this phase
    authorized_phase = decision_fm.get("authorized_phase", instruction_fm.get("phase", "phase1"))
    downstream_gates = [
        "10_execution_feedback.md (Executor fills after completion)",
        "11_acceptance_review.md (Orchestrator independent acceptance)",
        "12_lesson_proposal.md (post-acceptance)",
    ]

    work_order = {
        "schema_version": "1.0",
        "harness_version": "phase5",
        "not_an_execution_authorization": True,
        "task_id": task_id,
        "case_id": case_id,
        "phase": phase,
        "executor_type": str(instruction_fm.get("executor_type", "hermes")),
        "delivery_profile": str(instruction_fm.get("delivery_profile", "default")),
        "authorized_phase": str(authorized_phase),
        "created_at": now_iso(),
        "harness_root": str(ROOT),
        "case_dir": str(case_dir),
        "instruction_file": str(case_dir / "09_executor_instruction.md"),
        "execution_context": execution_context,
        "upstream_depends_on": upstream,
        "downstream_gates": downstream_gates,
        "goals": {
            "primary": extract_section(instruction_body, "Phase 目标").splitlines()[0]
            if extract_section(instruction_body, "Phase 目标")
            else f"Execute {phase} for {case_id}",
            "secondary": steps[:5],
        },
        "hard_constraints": forbidden or [
            "不登录、不填表、不提交、不删文件、不扩 scope",
        ],
        "soft_constraints": [],
        "acceptance_criteria": acceptance_raw,
        "failure_strategy": failure_strategy,
        "rollback_to": {
            "checkpoint_file": str(case_dir / rollback_checkpoint) if rollback_checkpoint else "",
            "description": "Revert to last known-good Harness state file",
        },
        "output_files": output_files,
        "write_to": ["cases/"],
        "intake_meta": {
            "status": intake_fm.get("status"),
            "risk_tier": intake_fm.get("risk_tier"),
            "case_type": intake_fm.get("case_type"),
            "court_verdict_tier": intake_fm.get("court_verdict_tier"),
        },
    }
    return work_order


def main() -> int:
    parser = argparse.ArgumentParser(description="Build structured JSON work order.")
    parser.add_argument("case_dir", help="Case directory path")
    parser.add_argument("--output", help="Output path (default: artifacts/work_order.json)")
    parser.add_argument("--check", action="store_true", help="Logic check without writing")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    if not case_dir.is_dir():
        print(f"ERROR: case directory not found: {case_dir}")
        return 1

    instruction = case_dir / "09_executor_instruction.md"
    if not instruction.is_file():
        print(f"WARN: {instruction} not found; work order will have empty goals")

    wo = build_work_order(case_dir)

    if args.check:
        assert wo.get("not_an_execution_authorization") is True
        assert "execution_authorized" not in wo
        print("build_work_order --check passed")
        return 0

    out_path = Path(args.output) if args.output else case_dir / "artifacts" / "work_order.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(wo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
