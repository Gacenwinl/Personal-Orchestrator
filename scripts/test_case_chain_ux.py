#!/usr/bin/env python3
"""Lightweight UX helpers tests (no pytest required)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import derive_owner_lifecycle, parse_team_ids_from_02  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sample = ROOT / "cases/samples/CASE-001-mems-career-direction"
    teams = parse_team_ids_from_02(sample)
    if len(teams) != 8:
        print(f"FAIL: expected 8 selected teams, got {len(teams)}: {teams}")
        return 1
    print(f"OK: parse_team_ids_from_02 -> {len(teams)} teams")

    phd = ROOT / "cases/active/CASE-20260603-msc-us-phd-agent-pi-outreach"
    if phd.is_dir():
        lc = derive_owner_lifecycle(phd)
        if lc["lifecycle"] not in ("analysis_complete", "completed"):
            print(f"FAIL: PhD lifecycle expected analysis_complete|completed, got {lc['lifecycle']}")
            return 1
        if lc["default_tab"] != "panel-owner-next":
            print(f"FAIL: PhD default_tab expected panel-owner-next, got {lc['default_tab']}")
            return 1
        if not lc.get("owner_actions"):
            print("FAIL: PhD case should have owner_actions from 07")
            return 1
        print(f"OK: PhD lifecycle={lc['lifecycle']} actions={len(lc['owner_actions'])}")

    print("test_case_chain_ux passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
