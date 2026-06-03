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
            "scripts/list_cases.py",
            "scripts/scaffold_team_blocks.py",
            "scripts/render_handoff.py",
            "scripts/render_case_dashboard.py",
            "scripts/case_sop_server.py",
            "scripts/court_launcher.py",
            "scripts/court_dispatch.py",
            "scripts/workflow_daemon.py",
            "scripts/build_work_order.py",
            "scripts/hermes_doctor.py",
            "scripts/start_case.py",
            "scripts/fork_case.py",
            "scripts/test_case_chain_ux.py",
            "scripts/lib/case_chain.py",
            "scripts/lib/dashboard_owner.py",
            "scripts/lib/dashboard_wizard.py",
            "scripts/smoke_test.py",
        ]
    )
    run([python, "scripts/case_sop_server.py", "--check"])
    run([python, "scripts/court_dispatch.py",
         "cases/samples/CASE-001-mems-career-direction", "--check"])
    run([python, "scripts/workflow_daemon.py",
         "--case", "cases/samples/CASE-001-mems-career-direction", "--check"])
    run([python, "scripts/build_work_order.py",
         "cases/samples/CASE-001-mems-career-direction", "--check"])
    run([python, "scripts/test_case_chain_ux.py"])
    run([python, "scripts/hermes_doctor.py", "--check"])

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

        blocks = list((case_dir / "artifacts" / "team_blocks").glob("*.md"))
        if len(blocks) < 4:
            raise RuntimeError(f"expected team blocks, got {len(blocks)}")

    run([python, "scripts/list_cases.py"])
    run(
        [
            python,
            "scripts/scaffold_team_blocks.py",
            "cases/samples/CASE-001-mems-career-direction",
        ]
    )
    handoff = subprocess.run(
        [
            python,
            "scripts/render_handoff.py",
            "cases/samples/CASE-001-mems-career-direction",
            "--force",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if handoff.returncode not in {0, 2}:
        print(handoff.stdout)
        print(handoff.stderr)
        handoff.check_returncode()

    run(
        [
            python,
            "scripts/render_case_dashboard.py",
            "cases/samples/CASE-001-mems-career-direction",
            "--force",
        ]
    )
    dash = ROOT / "cases/samples/CASE-001-mems-career-direction/artifacts/CASE_DASHBOARD.html"
    text = dash.read_text(encoding="utf-8")
    if "CASE-001-mems-career-direction" not in text:
        raise RuntimeError("dashboard missing case_id")
    if "panel-wizard" not in text:
        raise RuntimeError("dashboard missing interactive wizard panel")
    if "panel-owner-next" not in text:
        raise RuntimeError("dashboard missing owner-next panel")

    run(
        [
            python,
            "scripts/court_launcher.py",
            "cases/samples/CASE-001-mems-career-direction",
            "--force",
        ]
    )
    plan = (
        ROOT
        / "cases/samples/CASE-001-mems-career-direction/artifacts/COURT_LAUNCH_PLAN.md"
    )
    if not plan.is_file():
        raise RuntimeError("court launch plan not generated")

    print("\nSmoke tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
