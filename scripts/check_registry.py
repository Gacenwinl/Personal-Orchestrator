#!/usr/bin/env python3
"""Validate registry consistency without third-party YAML dependencies."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TEAM_REQUIRED_KEYS = {
    "team_id",
    "domain",
    "mandate",
    "applies_to_case_types",
    "excludes_case_types",
    "inputs",
    "outputs",
    "scoring_dimensions",
    "common_misjudgments",
    "recommended_model_profile",
    "conflicts_with",
}


def parse_top_level_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith(" ") or line.startswith("#"):
            continue
        if ":" in line:
            keys.add(line.split(":", 1)[0].strip())
    return keys


def parse_team_id(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("team_id:"):
            return line.split(":", 1)[1].strip()
    return None


def parse_modes(path: Path) -> set[str]:
    modes: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "- id:":
            continue
        match = re.match(r"\s+- id:\s*(\S+)", line)
        if match:
            modes.add(match.group(1))
        elif line.strip() == "id:" and index + 1 < len(lines):
            modes.add(lines[index + 1].strip())
    return modes


def parse_list_values(path: Path, field_names: set[str]) -> set[str]:
    values: set[str] = set()
    active = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "- when:":
            active = False
            continue
        if re.match(r"^[A-Za-z_]+:", stripped):
            key = stripped.split(":", 1)[0]
            active = key in field_names
            inline = stripped.split(":", 1)[1].strip()
            if active and inline and inline not in {"[]", "{}"}:
                values.add(inline)
            continue
        if active and stripped.startswith("- "):
            values.add(stripped[2:].strip())
    return values


def validate_registry(root: Path) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    teams_dir = root / "teams"
    team_files = sorted(teams_dir.glob("*.yaml"))
    if not team_files:
        errors.append("registry/teams contains no *.yaml files")

    team_ids: set[str] = set()
    for path in team_files:
        keys = parse_top_level_keys(path)
        missing = sorted(TEAM_REQUIRED_KEYS - keys)
        if missing:
            errors.append(f"{path}: missing keys: {', '.join(missing)}")

        team_id = parse_team_id(path)
        if team_id is None:
            errors.append(f"{path}: missing team_id value")
            continue
        if path.stem != team_id:
            errors.append(f"{path}: filename does not match team_id {team_id}")
        if team_id in team_ids:
            errors.append(f"duplicate team_id: {team_id}")
        team_ids.add(team_id)

    mode_ids = parse_modes(root / "debate_modes.yaml")
    if not mode_ids:
        errors.append("registry/debate_modes.yaml defines no modes")

    team_refs = parse_list_values(
        root / "team_selector_rules.yaml",
        {"required_teams", "optional_teams", "add_required"},
    )
    for ref in sorted(team_refs):
        if ref not in team_ids:
            errors.append(f"team_selector_rules.yaml references missing team: {ref}")

    mode_refs = parse_list_values(root / "mode_selector_rules.yaml", {"modes", "add_modes"})
    for ref in sorted(mode_refs):
        if ref not in mode_ids:
            errors.append(f"mode_selector_rules.yaml references missing mode: {ref}")

    required_team_refs = parse_required_team_values(root / "mode_selector_rules.yaml")
    for ref in sorted(required_team_refs):
        if ref not in team_ids:
            errors.append(f"mode_selector_rules.yaml require_team missing team: {ref}")

    print(f"teams: {len(team_ids)}")
    print(f"modes: {len(mode_ids)}")
    print(f"team rule refs: {len(team_refs)}")
    print(f"mode rule refs: {len(mode_refs)}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  WARN: {warning}")
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  ERROR: {error}")
        print(f"\nResult: FAIL ({len(errors)} errors)")
        return 1

    print("\nResult: PASS")
    return 0


def parse_required_team_values(path: Path) -> set[str]:
    refs: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("require_team:"):
            value = stripped.split(":", 1)[1].strip()
            if value:
                refs.add(value)
    return refs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate harness registry consistency.")
    parser.add_argument("--registry-dir", default="registry")
    args = parser.parse_args()
    return validate_registry(Path(args.registry_dir))


if __name__ == "__main__":
    raise SystemExit(main())
