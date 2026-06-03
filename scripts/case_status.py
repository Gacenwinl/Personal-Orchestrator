#!/usr/bin/env python3
"""Summarize a harness case's audit-chain progress and next action."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import chain_progress, next_action_text  # noqa: E402


def summarize(case_dir: Path) -> int:
    if not case_dir.is_dir():
        print(f"ERROR: case directory does not exist: {case_dir}")
        return 1

    present, missing, intake, decision = chain_progress(case_dir)

    print(f"case_dir: {case_dir}")
    print(f"case_id: {intake.get('case_id', '(unknown)')}")
    print(f"status: {intake.get('status', '(unknown)')}")
    print(f"case_type: {intake.get('case_type', '(unknown)')}")
    print(f"risk_tier: {intake.get('risk_tier', '(unknown)')}")
    print(f"needs_execution: {intake.get('needs_execution', '(unknown)')}")
    print(
        "execution_authorized: "
        f"{decision.get('execution_authorized', intake.get('execution_authorized', '(unknown)'))}"
    )
    print()

    print("present:")
    for _, rel, label in present:
        print(f"  OK   {rel} — {label}")

    print("\nmissing:")
    if missing:
        for _, rel, label in missing:
            print(f"  MISS {rel} — {label}")
    else:
        print("  none")

    print(f"\nnext_action: {next_action_text(missing, intake, decision)}")
    return 0 if not missing else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize harness case progress.")
    parser.add_argument("case_dir", help="Path to cases/.../CASE-... directory")
    args = parser.parse_args()
    return summarize(Path(args.case_dir))


if __name__ == "__main__":
    raise SystemExit(main())
