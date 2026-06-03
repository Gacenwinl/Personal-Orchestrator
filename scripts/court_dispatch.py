#!/usr/bin/env python3
"""Dispatch Harness court teams to Hermes kanban swarm for parallel evaluation.

Usage:
    python3 scripts/court_dispatch.py cases/active/CASE-xxx [--dry-run] [--check]
    make court-run CASE=cases/active/CASE-xxx
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    ROOT,
    parse_frontmatter,
    parse_team_ids_from_02,
)

HERMES = shutil.which("hermes") or str(
    Path.home() / "OpenClaw_Workspace/hermes/venv/bin/hermes"
)
KANBAN_BOARD = "orchestrator-court"

WORKER_PROFILE = "court-team"
VERIFIER_PROFILE = "court-verify"
SYNTHESIZER_PROFILE = "court-synthesize"
SKILL_NAME = "harness-court-team"


def check_hermes() -> str:
    """Return hermes path or raise."""
    p = Path(HERMES)
    if not p.is_file():
        raise FileNotFoundError(
            f"hermes not found at {HERMES}. Run `make hermes-setup` first."
        )
    return str(p)


def check_profiles(hermes: str, dry_run: bool) -> None:
    """Verify required profiles exist; print setup hint if missing."""
    result = subprocess.run(
        [hermes, "profile", "list", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("WARN: could not list hermes profiles; skipping profile check")
        return
    try:
        profiles_raw = json.loads(result.stdout)
        names = {p.get("name", "") for p in profiles_raw} if isinstance(profiles_raw, list) else set()
    except (json.JSONDecodeError, AttributeError):
        # profile list may output plain text
        names = set(result.stdout.splitlines())

    missing = [
        p
        for p in [WORKER_PROFILE, VERIFIER_PROFILE, SYNTHESIZER_PROFILE]
        if p not in names
    ]
    if missing:
        print(
            f"WARN: Hermes profiles not found: {missing}\n"
            "Run `make hermes-setup` to create them.\n"
            "Proceeding with --dry-run to show kanban swarm command only."
        )
        if not dry_run:
            raise RuntimeError(
                f"Missing profiles: {missing}. Run `make hermes-setup` first."
            )


def init_board(hermes: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] hermes kanban init --board {KANBAN_BOARD}")
        return
    subprocess.run([hermes, "kanban", "init"], check=False)


def dispatch_swarm(
    case_dir: Path,
    case_id: str,
    teams: list[str],
    hermes: str,
    dry_run: bool,
    idempotency_key: str | None = None,
) -> dict:
    """Build and optionally run hermes kanban swarm command."""
    goal = (
        f"对 Harness 案件 {case_id} 进行多队法庭评审，"
        f"产出各队 team_block（artifacts/team_blocks/）及汇总 05_court_summary.md。"
        f"案件目录：{case_dir}"
    )
    idem_key = idempotency_key or f"{case_id}-court"

    args: list[str] = [
        hermes, "kanban", "swarm",
        goal,
        "--verifier", VERIFIER_PROFILE,
        "--synthesizer", SYNTHESIZER_PROFILE,
        "--idempotency-key", idem_key,
        "--json",
    ]

    for team_id in teams:
        title = f"{team_id}::{case_dir}"
        args += ["--worker", f"{WORKER_PROFILE}:{title}:{SKILL_NAME}"]

    print("kanban swarm command:")
    safe = [a if "::" not in a else f'"{a}"' for a in args]
    print("  " + " ".join(safe))

    if dry_run:
        print("[dry-run] command not executed")
        return {"dry_run": True, "teams": teams, "case_id": case_id}

    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: hermes kanban swarm failed:\n{result.stderr}", flush=True)
        sys.exit(1)

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw": result.stdout.strip()}

    print(f"Swarm created: {json.dumps(data, ensure_ascii=False, indent=2)}")
    return data


def write_dispatch_record(case_dir: Path, data: dict, teams: list[str]) -> Path:
    """Write artifacts/court_dispatch.json for workflow_daemon to track."""
    out = case_dir / "artifacts" / "court_dispatch.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "teams": teams,
        "swarm_result": data,
        "status": "dispatched",
    }
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Dispatch record: {out}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Dispatch court swarm via Hermes kanban.")
    parser.add_argument("case_dir", help="Path to case directory")
    parser.add_argument("--dry-run", action="store_true", help="Print command without running")
    parser.add_argument("--check", action="store_true", help="API logic smoke (no hermes call)")
    parser.add_argument("--idempotency-key", help="Override kanban idempotency key")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    if not case_dir.is_dir():
        print(f"ERROR: case directory not found: {case_dir}")
        return 1

    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    case_id = intake.get("case_id", case_dir.name)
    teams = parse_team_ids_from_02(case_dir)

    if not teams:
        print(f"ERROR: no teams found in {case_dir}/02_team_selection.md")
        print("Hint: run `python3 scripts/suggest_teams.py <case_dir> --write` first")
        return 1

    print(f"case_id: {case_id}")
    print(f"teams ({len(teams)}): {teams}")

    if args.check:
        print("court_dispatch --check passed")
        return 0

    hermes = check_hermes()
    dry = args.dry_run
    check_profiles(hermes, dry_run=dry)
    init_board(hermes, dry_run=dry)
    data = dispatch_swarm(
        case_dir, case_id, teams, hermes, dry_run=dry,
        idempotency_key=args.idempotency_key,
    )
    if not dry:
        write_dispatch_record(case_dir, data, teams)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
