#!/usr/bin/env python3
"""Suggest expert teams for a harness case.

The script reads a case's `01_case_intake.md` plus
`registry/team_selector_rules.yaml` and prints the matched required/optional
teams. It is a helper for Orchestrator, not an execution authority.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TeamRule:
    index: int
    when: dict[str, Any] = field(default_factory=dict)
    required_teams: list[str] = field(default_factory=list)
    optional_teams: list[str] = field(default_factory=list)
    add_required: list[str] = field(default_factory=list)
    max_teams: int | None = None


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


def parse_team_rules(path: Path) -> list[TeamRule]:
    rules: list[TeamRule] = []
    current: TeamRule | None = None
    section: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if indent == 2 and stripped == "- when:":
            current = TeamRule(index=len(rules) + 1)
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
            if section in {"required_teams", "optional_teams", "add_required"}:
                getattr(current, section).append(item)
            continue

        if indent == 6 and ":" in stripped and section == "when":
            key, value = stripped.split(":", 1)
            current.when[key.strip()] = parse_scalar(value.strip())
            continue

        if indent == 4 and stripped.startswith("max_teams:"):
            _, value = stripped.split(":", 1)
            parsed = parse_scalar(value.strip())
            if isinstance(parsed, int):
                current.max_teams = parsed

    return rules


def rule_matches(rule: TeamRule, intake: dict[str, Any], pre_execution: bool) -> bool:
    for key, expected in rule.when.items():
        if key == "pre_execution":
            actual = pre_execution
        else:
            actual = intake.get(key)
        if actual != expected:
            return False
    return True


def unique_extend(target: list[str], items: list[str]) -> None:
    for item in items:
        if item not in target:
            target.append(item)


def suggest(case_dir: Path, registry_dir: Path, pre_execution: bool) -> int:
    intake_path = case_dir / "01_case_intake.md"
    rules_path = registry_dir / "team_selector_rules.yaml"

    intake = parse_frontmatter(intake_path)
    rules = parse_team_rules(rules_path)
    required: list[str] = []
    optional: list[str] = []
    matched: list[TeamRule] = []
    max_teams: int | None = None

    for rule in rules:
        if not rule_matches(rule, intake, pre_execution):
            continue
        matched.append(rule)
        unique_extend(required, rule.required_teams)
        unique_extend(required, rule.add_required)
        unique_extend(optional, rule.optional_teams)
        if rule.max_teams is not None:
            max_teams = rule.max_teams

    optional = [team for team in optional if team not in required]

    print(f"case_id: {intake.get('case_id')}")
    print(f"case_type: {intake.get('case_type')}")
    print(f"risk_tier: {intake.get('risk_tier')}")
    print(f"pre_execution: {str(pre_execution).lower()}")
    print()

    if not matched:
        print("matched_rules: none")
        print("required_teams: []")
        print("optional_teams: []")
        return 2

    print("matched_rules:")
    for rule in matched:
        conditions = ", ".join(f"{key}={value}" for key, value in rule.when.items())
        print(f"  - rule_{rule.index}: {conditions}")

    print("\nrequired_teams:")
    for team in required:
        print(f"  - {team}")

    print("\noptional_teams:")
    if optional:
        for team in optional:
            print(f"  - {team}")
    else:
        print("  - none")

    if max_teams is not None:
        print(f"\nmax_teams: {max_teams}")

    if max_teams is not None and len(required) > max_teams:
        print(
            f"\nWARNING: required team count ({len(required)}) exceeds max_teams ({max_teams})",
            file=sys.stderr,
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest harness expert teams.")
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
    args = parser.parse_args(argv)

    try:
        return suggest(Path(args.case_dir), Path(args.registry_dir), args.pre_execution)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
