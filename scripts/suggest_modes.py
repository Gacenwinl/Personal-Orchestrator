#!/usr/bin/env python3
"""Suggest debate modes for a harness case.

Reads `01_case_intake.md` and `registry/mode_selector_rules.yaml`.
The output is advisory for Orchestrator and must be copied into
`02b_mode_selection.md` with human-readable reasons.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ModeRule:
    index: int
    when: dict[str, Any] = field(default_factory=dict)
    modes: list[str] = field(default_factory=list)
    add_modes: list[str] = field(default_factory=list)
    require_team: str | None = None
    notes: str | None = None


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"missing frontmatter: {path}")
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
    if value.isdigit():
        return int(value)
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def parse_mode_rules(path: Path) -> list[ModeRule]:
    rules: list[ModeRule] = []
    current: ModeRule | None = None
    section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if indent == 2 and stripped == "- when:":
            current = ModeRule(index=len(rules) + 1)
            rules.append(current)
            section = "when"
            continue

        if current is None:
            continue

        if indent == 4 and stripped.endswith(":"):
            section = stripped[:-1]
            continue

        if indent == 6 and stripped.startswith("- "):
            item = stripped[2:].strip()
            if section in {"modes", "add_modes"}:
                getattr(current, section).append(item)
            continue

        if indent == 6 and ":" in stripped and section == "when":
            key, value = stripped.split(":", 1)
            current.when[key.strip()] = parse_scalar(value.strip())
            continue

        if indent == 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = parse_scalar(value.strip())
            if key == "require_team":
                current.require_team = str(value)
            elif key == "notes":
                current.notes = str(value)

    return rules


def rule_matches(rule: ModeRule, intake: dict[str, Any], pre_execution: bool) -> bool:
    for key, expected in rule.when.items():
        if key == "pre_execution":
            actual = pre_execution
        elif key == "internal_conflict_score_gte":
            return False
        else:
            actual = intake.get(key)
        if actual != expected:
            return False
    return True


def unique_extend(target: list[str], items: list[str]) -> None:
    for item in items:
        if item not in target:
            target.append(item)


def suggest(
    case_dir: Path,
    registry_dir: Path,
    pre_execution: bool,
    write: bool = False,
    force: bool = False,
) -> int:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    rules = parse_mode_rules(registry_dir / "mode_selector_rules.yaml")

    modes: list[str] = []
    required_teams: list[str] = []
    matched: list[ModeRule] = []

    for rule in rules:
        if not rule_matches(rule, intake, pre_execution):
            continue
        matched.append(rule)
        unique_extend(modes, rule.modes)
        unique_extend(modes, rule.add_modes)
        if rule.require_team and rule.require_team not in required_teams:
            required_teams.append(rule.require_team)

    print(f"case_id: {intake.get('case_id')}")
    print(f"case_type: {intake.get('case_type')}")
    print(f"risk_tier: {intake.get('risk_tier')}")
    print(f"needs_execution: {str(bool(intake.get('needs_execution'))).lower()}")
    print(f"pre_execution: {str(pre_execution).lower()}")
    print()

    if not matched:
        print("matched_rules: none")
        print("suggested_modes: []")
        return 2

    print("matched_rules:")
    for rule in matched:
        conditions = ", ".join(f"{key}={value}" for key, value in rule.when.items())
        suffix = f" — {rule.notes}" if rule.notes else ""
        print(f"  - rule_{rule.index}: {conditions}{suffix}")

    print("\nsuggested_modes:")
    for mode in modes:
        print(f"  - {mode}")

    print("\nrequired_teams_from_modes:")
    if required_teams:
        for team in required_teams:
            print(f"  - {team}")
    else:
        print("  - none")

    if write:
        write_mode_selection(case_dir, matched, modes, required_teams, pre_execution, force)
        print(f"\nwrote: {case_dir / '02b_mode_selection.md'}")

    return 0


def write_mode_selection(
    case_dir: Path,
    matched: list[ModeRule],
    modes: list[str],
    required_teams: list[str],
    pre_execution: bool,
    force: bool,
) -> None:
    target = case_dir / "02b_mode_selection.md"
    if target.exists() and not force:
        raise FileExistsError(f"{target} already exists; pass --force to overwrite")

    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    mode_lines = "\n".join(f"{index}. {mode}" for index, mode in enumerate(modes, 1))
    if not mode_lines:
        mode_lines = "1. TODO: no mode rule matched"

    matched_lines = "\n".join(
        f"- rule_{rule.index}: "
        + ", ".join(f"{key}={value}" for key, value in rule.when.items())
        + (f" — {rule.notes}" if rule.notes else "")
        for rule in matched
    )
    required_team_lines = "\n".join(f"- {team}" for team in required_teams) or "- none"

    target.write_text(
        f"""---
case_id: {intake.get('case_id')}
rule_ref: registry/mode_selector_rules.yaml
generated_by: scripts/suggest_modes.py
pre_execution: {str(pre_execution).lower()}
---

# Mode Selection

## 模式序列（有序）

{mode_lines}

## 选择理由

{matched_lines}

## 模式要求的团队

{required_team_lines}

## 预计时间成本

- TODO: Orchestrator 结合案件复杂度填写。

## 模型分配（Phase 1 手填，见 model_routing_rules.yaml）

| 步骤 | vendor | 角色 |
|------|--------|------|
| TODO | TODO | TODO |
""",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest harness debate modes.")
    parser.add_argument("case_dir", help="Path to cases/.../CASE-... directory")
    parser.add_argument(
        "--registry-dir",
        default="registry",
        help="Path to registry directory (default: registry)",
    )
    parser.add_argument(
        "--pre-execution",
        action="store_true",
        help="Also apply pre_execution rules for reviewing a draft executor instruction",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write 02b_mode_selection.md draft into the case directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --write to overwrite an existing 02b_mode_selection.md",
    )
    args = parser.parse_args(argv)

    try:
        return suggest(
            Path(args.case_dir),
            Path(args.registry_dir),
            args.pre_execution,
            write=args.write,
            force=args.force,
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
