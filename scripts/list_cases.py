#!/usr/bin/env python3
"""List harness cases under cases/active and cases/samples."""

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


def collect_cases(root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    if not root.is_dir():
        return rows
    for case_dir in sorted(root.iterdir()):
        if not case_dir.is_dir() or case_dir.name.startswith("."):
            continue
        intake = parse_frontmatter(case_dir / "01_case_intake.md")
        rows.append((root.name, case_dir, intake))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="List harness cases.")
    parser.add_argument(
        "--roots",
        nargs="*",
        default=["cases/active", "cases/samples"],
        help="Directories to scan (default: active + samples)",
    )
    args = parser.parse_args()

    all_rows: list[tuple[str, Path, dict[str, Any]]] = []
    for rel in args.roots:
        all_rows.extend(collect_cases(Path(rel)))

    if not all_rows:
        print("No cases found.")
        return 0

    print(f"{'bucket':<10} {'case_id':<40} {'status':<18} {'risk':<8} path")
    print("-" * 110)
    for bucket, case_dir, intake in all_rows:
        case_id = intake.get("case_id", case_dir.name)
        status = intake.get("status", "(no intake)")
        risk = intake.get("risk_tier", "-")
        print(f"{bucket:<10} {case_id:<40} {status:<18} {risk:<8} {case_dir}")
    print(f"\ntotal: {len(all_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
