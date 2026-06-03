#!/usr/bin/env python3
"""Create a new Markdown harness case skeleton from a topic.

This is intentionally conservative: it only creates local Markdown files under
`cases/active/` and does not invoke models, Hermes, APIs, or external tasks.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


VALID_RISK = {"low", "medium", "high", "critical"}


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        return "case"
    # Keep paths readable without overfitting Chinese tokenization.
    return value[:48].strip("-") or "case"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def create_case(
    topic: str,
    case_type: str,
    risk_tier: str,
    needs_execution: bool,
    cases_root: Path,
    slug: str | None,
) -> Path:
    if risk_tier not in VALID_RISK:
        raise ValueError(f"risk_tier must be one of: {', '.join(sorted(VALID_RISK))}")

    case_slug = slugify(slug or topic)
    case_id = f"CASE-{date.today().strftime('%Y%m%d')}-{case_slug}"
    case_dir = cases_root / case_id
    if case_dir.exists():
        raise FileExistsError(f"case already exists: {case_dir}")

    (case_dir / "artifacts" / "team_blocks").mkdir(parents=True)
    (case_dir / "inputs").mkdir()
    (case_dir / "outputs").mkdir()

    human_gate = needs_execution or risk_tier in {"high", "critical"}
    cac_required = risk_tier in {"high", "critical"}

    write_text(
        case_dir / "00_owner_intent.md",
        f"""---
case_id: {case_id}
recorded_at: {date.today().isoformat()}
---

# Owner Intent（原始意图）

## 用户原话（优先逐字）

> {topic}

## 上下文（可选）

- 

## Orchestrator 理解（非结论）

- 用户似乎在问：
- 明确不属于本案的：
""",
    )

    write_text(
        case_dir / "01_case_intake.md",
        f"""---
case_id: {case_id}
status: draft
case_type: {case_type}
risk_tier: {risk_tier}
topic: "{topic}"
owner_intent_ref: 00_owner_intent.md

needs_execution: {bool_text(needs_execution)}
execution_authorized: false
authorized_phase: null
human_approval_required: {bool_text(human_gate)}

court_verdict_tier: null
cac_required: {bool_text(cac_required)}
cac_exempt_reason: null
---

# Case Intake

## 案件摘要

（Orchestrator 填写：一句话问题陈述）

## 成功标准

- 

## 约束与时间预算

- 

## 输入清单

| 文件 | 说明 |
|------|------|
| | |

## 不适用说明

（本案件明确不做什么）
""",
    )

    write_text(
        case_dir / "CASE_TODO.md",
        f"""# {case_id} 下一步

1. 审阅并补充 `02_team_selection.md` / `02b_mode_selection.md` 中的 TODO 理由。
2. 审阅 `artifacts/team_blocks/*.md`，按各团队 registry 定义填写 04 结构。
3. 按 `engine/ORCHESTRATOR_RUNBOOK.md` 继续 03、05–12。
4. 授权执行后：`python3 scripts/render_handoff.py {case_dir}`
5. 结案前：`python3 scripts/validate_case.py {case_dir}`
""",
    )

    return case_dir


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new harness case skeleton.")
    parser.add_argument("topic", help="Raw owner topic or intent")
    parser.add_argument("--case-type", default="career_direction")
    parser.add_argument("--risk-tier", default="medium", choices=sorted(VALID_RISK))
    parser.add_argument("--needs-execution", action="store_true")
    parser.add_argument("--cases-root", default="cases/active")
    parser.add_argument("--slug", help="Optional path-safe case slug")
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Also generate 02_team_selection.md and 02b_mode_selection.md drafts",
    )
    args = parser.parse_args()

    case_dir = create_case(
        topic=args.topic,
        case_type=args.case_type,
        risk_tier=args.risk_tier,
        needs_execution=args.needs_execution,
        cases_root=Path(args.cases_root),
        slug=args.slug,
    )
    if args.prepare:
        script_dir = Path(__file__).resolve().parent
        run_helper(script_dir / "suggest_teams.py", case_dir, "--write")
        run_helper(script_dir / "suggest_modes.py", case_dir, "--write")
        run_helper(script_dir / "scaffold_team_blocks.py", case_dir)

    rel = case_dir.relative_to(Path.cwd()) if case_dir.is_relative_to(Path.cwd()) else case_dir
    print(case_dir)
    print(f"\n下一步: make dashboard CASE={rel}")
    print(f"打开索引: open cases/index.html")
    print("可选: make sop-console")
    return 0


def run_helper(script: Path, case_dir: Path, *extra: str) -> None:
    subprocess.run(
        [sys.executable, str(script), str(case_dir), *extra],
        check=True,
    )


if __name__ == "__main__":
    raise SystemExit(main())
