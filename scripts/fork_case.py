#!/usr/bin/env python3
"""Fork a new case from an existing one (same 00 intent, fresh court chain)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract_topic_from_intent(case_dir: Path) -> str:
    path = case_dir / "00_owner_intent.md"
    if not path.is_file():
        return case_dir.name
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith(">"):
            return line.strip().lstrip(">").strip()
    intake = case_dir / "01_case_intake.md"
    if intake.is_file():
        m = re.search(r"^topic:\s*(.+)$", intake.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip()
    return case_dir.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Fork case with clean directory.")
    parser.add_argument("source_case", help="Existing case directory")
    parser.add_argument("--slug", help="Slug suffix (default: fork)")
    parser.add_argument("--case-type", help="Override case type from source intake")
    parser.add_argument("--risk-tier", help="Override risk tier")
    parser.add_argument("--needs-execution", action="store_true")
    args = parser.parse_args()

    source = Path(args.source_case).resolve()
    if not source.is_dir():
        print(f"ERROR: not found: {source}")
        return 1

    topic = extract_topic_from_intent(source)
    slug = args.slug or f"fork-{source.name[-20:]}"

    intake_fm: dict[str, str] = {}
    intake_path = source / "01_case_intake.md"
    if intake_path.is_file():
        for line in intake_path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                intake_fm[k.strip()] = v.strip()

    case_type = args.case_type or intake_fm.get("case_type", "career_direction")
    risk = args.risk_tier or intake_fm.get("risk_tier", "high")
    needs = args.needs_execution or intake_fm.get("needs_execution") == "true"

    cmd = [
        sys.executable,
        str(ROOT / "scripts/start_case.py"),
        topic,
        "--case-type",
        case_type,
        "--risk-tier",
        risk,
        "--slug",
        slug,
    ]
    if needs:
        cmd.append("--needs-execution")

    print(f"Forking from {source.name} → new case")
    print(f"Topic: {topic[:80]}...")
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
