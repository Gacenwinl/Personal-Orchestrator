#!/usr/bin/env python3
"""Render a Hermes handoff packet from 09_executor_instruction.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any


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
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value == "true":
            data[key.strip()] = True
        elif value == "false":
            data[key.strip()] = False
        elif value in {"null", "~", ""}:
            data[key.strip()] = None
        else:
            data[key.strip()] = value.strip('"')
    return data


def bool_text(value: Any) -> str:
    return "true" if value is True else "false"


def render(case_dir: Path, output: Path | None, force: bool) -> int:
    instruction = case_dir / "09_executor_instruction.md"
    if not instruction.is_file():
        print(f"ERROR: missing {instruction}", flush=True)
        return 1

    inst_fm = parse_frontmatter(instruction)
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")

    authorized = decision.get("execution_authorized", intake.get("execution_authorized"))
    human_gate = decision.get("human_approval_required", intake.get("human_approval_required"))
    phase = inst_fm.get("phase", decision.get("authorized_phase", intake.get("authorized_phase")))

    if authorized is not True:
        print(
            "WARNING: execution_authorized is not true; handoff packet is for review only.",
            flush=True,
        )

    target = output or case_dir / "artifacts" / f"HANDOFF_hermes_{phase or 'phase'}.md"
    if target.exists() and not force:
        raise FileExistsError(f"{target} exists; pass --force to overwrite")

    target.parent.mkdir(parents=True, exist_ok=True)
    body = instruction.read_text(encoding="utf-8")

    packet = f"""---
case_id: {intake.get('case_id', case_dir.name)}
phase: {phase}
executor_target: hermes
execution_authorized: {bool_text(authorized)}
human_approval_required: {bool_text(human_gate)}
generated_by: scripts/render_handoff.py
---

# Hermes Handoff Packet

> **这不是 court verdict，也不是自动执行令。** 仅当 `execution_authorized: true` 且 Owner 已按需审批后，才可交给 Hermes。

## 授权检查

| 项 | 值 |
|----|-----|
| execution_authorized | {authorized} |
| authorized_phase | {phase} |
| human_approval_required | {human_gate} |
| court_verdict_tier | {intake.get('court_verdict_tier', '(see 05)')} |

## 交给 Hermes 前确认

- [ ] 已读 `constraints/HARNESS_ENGINE.md`
- [ ] `09` 中 forbidden_actions 与 Hermes profile 白名单一致
- [ ] 不修改 Hermes 源码，不自动创建 cron（除非你明确批准）
- [ ] 执行后只更新 Harness `10_execution_feedback.md`，由 Orchestrator 填 `11`

## 任务书原文

{body}

## 执行后回报

请将结果写入本案：

- `{case_dir / '10_execution_feedback.md'}`
- 产物放到 `outputs/` 下约定路径
"""
    target.write_text(packet, encoding="utf-8")
    print(target)
    return 0 if authorized is True else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Hermes handoff packet.")
    parser.add_argument("case_dir", help="Path to CASE-... directory")
    parser.add_argument("-o", "--output", help="Output path (default: artifacts/HANDOFF_hermes_<phase>.md)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        return render(Path(args.case_dir), Path(args.output) if args.output else None, args.force)
    except OSError as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
