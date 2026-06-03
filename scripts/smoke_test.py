#!/usr/bin/env python3
"""Run local smoke tests for the Markdown harness helpers."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().strftime("%Y%m%d")


def run(command: list[str]) -> None:
    print("$ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    python = sys.executable

    run(
        [
            python,
            "scripts/check_registry.py",
        ]
    )
    run(
        [
            python,
            "scripts/check_templates.py",
        ]
    )
    run(
        [
            python,
            "scripts/validate_case.py",
            "cases/samples/CASE-001-mems-career-direction",
        ]
    )
    run(
        [
            python,
            "scripts/suggest_teams.py",
            "cases/samples/CASE-001-mems-career-direction",
        ]
    )
    run(
        [
            python,
            "scripts/suggest_modes.py",
            "cases/samples/CASE-001-mems-career-direction",
        ]
    )
    run(
        [
            python,
            "scripts/case_status.py",
            "cases/samples/CASE-001-mems-career-direction",
        ]
    )
    run(
        [
            python,
            "-m",
            "py_compile",
            "scripts/validate_case.py",
            "scripts/suggest_teams.py",
            "scripts/suggest_modes.py",
            "scripts/new_case.py",
            "scripts/case_status.py",
            "scripts/check_registry.py",
            "scripts/check_templates.py",
            "scripts/smoke_test.py",
        ]
    )

    with tempfile.TemporaryDirectory() as tmp:
        case_dir = Path(tmp) / f"CASE-{TODAY}-smoke-test"
        run(
            [
                python,
                "scripts/new_case.py",
                "测试 topic：smoke test",
                "--case-type",
                "career_direction",
                "--risk-tier",
                "high",
                "--needs-execution",
                "--prepare",
                "--cases-root",
                tmp,
                "--slug",
                "smoke-test",
            ]
        )
        for rel in [
            "00_owner_intent.md",
            "01_case_intake.md",
            "02_team_selection.md",
            "02b_mode_selection.md",
            "CASE_TODO.md",
        ]:
            path = case_dir / rel
            if not path.is_file():
                raise FileNotFoundError(path)

    print("\nSmoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
