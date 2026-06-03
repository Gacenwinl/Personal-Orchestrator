#!/usr/bin/env python3
"""Generate per-team court launch plan for manual Cursor sessions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    ROOT,
    load_wizard_registry,
    parse_frontmatter,
    parse_team_ids_from_02,
)

DEFAULT_COURT_TEMPLATE = """\
你是 {team_id} 评审队。读 registry/teams/{team_id}.yaml 与 {case_dir}/01_case_intake.md。
只填 {case_dir}/artifacts/team_blocks/{team_id}.md（templates/04）。
禁止设置 execution_authorized 或写 09。"""


def build_launch_plan(case_dir: Path) -> str:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    case_id = intake.get("case_id", case_dir.name)
    reg = load_wizard_registry()
    template = (reg.get("court_invoke_template") or DEFAULT_COURT_TEMPLATE).strip()
    teams = parse_team_ids_from_02(case_dir)
    if not teams:
        teams = sorted(
            p.stem for p in (case_dir / "artifacts" / "team_blocks").glob("*.md")
        )

    lines = [
        "---",
        f"case_id: {case_id}",
        "generated_by: scripts/court_launcher.py",
        "---",
        "",
        "# Court Launch Plan",
        "",
        "> 每队 **单独开 Cursor Session** 执行，不自动调用 API。",
        "",
        "| team_id | block_path | status |",
        "|---------|------------|--------|",
    ]
    for team_id in teams:
        block = f"artifacts/team_blocks/{team_id}.md"
        prompt = template.replace("{team_id}", team_id).replace(
            "{case_dir}", str(case_dir.relative_to(ROOT))
        )
        lines.append(f"| {team_id} | {block} | pending |")
        lines.append("")
        lines.append(f"## {team_id}")
        lines.append("")
        lines.append("```text")
        lines.append(prompt)
        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate court launch plan.")
    parser.add_argument("case_dir", help="Case directory")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    out = case_dir / "artifacts" / "COURT_LAUNCH_PLAN.md"
    if out.exists() and not args.force:
        print(f"ERROR: {out} exists; use --force", flush=True)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_launch_plan(case_dir), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
