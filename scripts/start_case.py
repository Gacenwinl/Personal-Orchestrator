#!/usr/bin/env python3
"""One-shot: new case + dashboard + index refresh."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a new harness case with dashboard.")
    parser.add_argument("topic", help="Owner topic / intent")
    parser.add_argument("--case-type", default="career_direction")
    parser.add_argument("--risk-tier", default="high")
    parser.add_argument("--needs-execution", action="store_true")
    parser.add_argument("--slug", help="Optional slug")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        str(ROOT / "scripts/new_case.py"),
        args.topic,
        "--case-type",
        args.case_type,
        "--risk-tier",
        args.risk_tier,
        "--prepare",
    ]
    if args.needs_execution:
        cmd.append("--needs-execution")
    if args.slug:
        cmd.extend(["--slug", args.slug])

    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return result.returncode

    case_dir = ""
    for line in result.stdout.splitlines():
        p = Path(line.strip())
        if p.is_dir() and "CASE-" in p.name:
            case_dir = str(p.resolve())
            break
    if not case_dir:
        print("ERROR: could not determine case_dir from new_case output", file=sys.stderr)
        return 1

    rel = Path(case_dir).relative_to(ROOT) if Path(case_dir).is_absolute() else Path(case_dir)

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/render_case_dashboard.py"), str(rel), "--force"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/render_case_dashboard.py"), "--index", "--force"],
        cwd=ROOT,
        check=True,
    )

    print("\n--- 下一步 ---")
    print(f"CASE={rel}")
    print(f"make dashboard CASE={rel}")
    print(f"open {ROOT / 'cases/index.html'}")
    print("可选: make sop-console")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
