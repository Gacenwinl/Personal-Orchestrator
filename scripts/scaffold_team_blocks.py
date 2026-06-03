#!/usr/bin/env python3
"""Scaffold team verdict block files from 02_team_selection.md."""

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
        data[key.strip()] = value.strip().strip('"')
    return data


def parse_selected_teams(selection_path: Path) -> list[str]:
    text = selection_path.read_text(encoding="utf-8")
    teams: list[str] = []
    in_section = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## 选用团队"):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("|"):
            continue
        if "team_id" in line or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or not cells[0]:
            continue
        team_id = cells[0]
        if team_id in {"（无）", "TODO"}:
            continue
        teams.append(team_id)
    return teams


def render_block(case_id: str, team_id: str, template: str) -> str:
    return (
        template.replace("{{team_id}}", team_id)
        .replace("TEAM_ID", team_id)
        .replace('case_id: ""', f'case_id: {case_id}')
        .replace('team_id: ""', f"team_id: {team_id}")
        .replace(
            "registry_ref: registry/teams/TEAM_ID.yaml",
            f"registry_ref: registry/teams/{team_id}.yaml",
        )
    )


def scaffold(case_dir: Path, template_dir: Path, force: bool) -> int:
    selection = case_dir / "02_team_selection.md"
    if not selection.is_file():
        print(f"ERROR: missing {selection}", flush=True)
        return 1

    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    case_id = intake.get("case_id", case_dir.name)
    teams = parse_selected_teams(selection)
    if not teams:
        print("ERROR: no teams found under '## 选用团队'", flush=True)
        return 1

    template = (template_dir / "04_team_verdict_block.md").read_text(encoding="utf-8")
    out_dir = case_dir / "artifacts" / "team_blocks"
    out_dir.mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    for team_id in teams:
        target = out_dir / f"{team_id}.md"
        if target.exists() and not force:
            skipped += 1
            continue
        target.write_text(render_block(case_id, team_id, template), encoding="utf-8")
        created += 1
        print(f"  wrote {target.relative_to(case_dir)}")

    print(f"\ncase_id: {case_id}")
    print(f"teams: {len(teams)}")
    print(f"created: {created}")
    print(f"skipped: {skipped}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold team verdict blocks.")
    parser.add_argument("case_dir", help="Path to CASE-... directory")
    parser.add_argument("--template-dir", default="templates")
    parser.add_argument("--force", action="store_true", help="Overwrite existing blocks")
    args = parser.parse_args()
    return scaffold(Path(args.case_dir), Path(args.template_dir), args.force)


if __name__ == "__main__":
    raise SystemExit(main())
