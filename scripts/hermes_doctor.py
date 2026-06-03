#!/usr/bin/env python3
"""Check local Hermes readiness for Harness Phase 5 automation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERMES = shutil.which("hermes") or str(
    Path.home() / "OpenClaw_Workspace/hermes/venv/bin/hermes"
)
REQUIRED_PROFILES = ("court-team", "court-verify", "court-synthesize")
SKILL_NAME = "harness-court-team"


def _env_has_api_key() -> bool:
    for key in ("XIAOMI_API_KEY", "XIAOMI_TOKEN_PLAN_CN_API_KEY"):
        if os.environ.get(key):
            return True
    env_path = Path.home() / ".openclaw" / ".env"
    if not env_path.is_file():
        return False
    text = env_path.read_text(encoding="utf-8")
    for key in ("XIAOMI_API_KEY", "XIAOMI_TOKEN_PLAN_CN_API_KEY"):
        for line in text.splitlines():
            if line.strip().startswith(f"{key}=") and "=" in line:
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return True
    return False


def run_check() -> dict:
    checks: list[dict[str, str]] = []
    ok_count = 0

    hermes_path = Path(HERMES)
    if hermes_path.is_file():
        checks.append({"id": "hermes_bin", "status": "ok", "detail": str(hermes_path)})
        ok_count += 1
    else:
        checks.append(
            {
                "id": "hermes_bin",
                "status": "fail",
                "detail": f"not found: {HERMES}",
            }
        )

    profile_names: set[str] = set()
    if hermes_path.is_file():
        result = subprocess.run(
            [str(hermes_path), "profile", "list"],
            capture_output=True,
            text=True,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("─") or "Profile" in line:
                continue
            profile_names.add(line.lstrip("◆").split()[0])

    for prof in REQUIRED_PROFILES:
        if prof in profile_names:
            checks.append({"id": f"profile_{prof}", "status": "ok", "detail": prof})
            ok_count += 1
        else:
            checks.append(
                {
                    "id": f"profile_{prof}",
                    "status": "fail",
                    "detail": f"missing profile {prof}",
                }
            )

    skill_ok = False
    if hermes_path.is_file():
        result = subprocess.run(
            [str(hermes_path), "skills", "list"],
            capture_output=True,
            text=True,
        )
        if SKILL_NAME in result.stdout:
            skill_ok = True
    if skill_ok:
        checks.append({"id": "skill", "status": "ok", "detail": SKILL_NAME})
        ok_count += 1
    else:
        checks.append(
            {
                "id": "skill",
                "status": "warn",
                "detail": f"{SKILL_NAME} not found in hermes skills list",
            }
        )

    if _env_has_api_key():
        checks.append({"id": "api_key", "status": "ok", "detail": "XIAOMI key present"})
        ok_count += 1
    else:
        checks.append(
            {
                "id": "api_key",
                "status": "warn",
                "detail": "XIAOMI_API_KEY not in env or ~/.openclaw/.env",
            }
        )

    total = len(checks)
    fails = sum(1 for c in checks if c["status"] == "fail")
    if fails:
        level = "bad"
        summary = f"Hermes 未就绪（{fails} 项失败）。运行 make hermes-setup"
    elif ok_count < total:
        level = "warn"
        summary = "Hermes 部分就绪；自动法庭前建议 make hermes-setup"
    else:
        level = "ok"
        summary = "Hermes 就绪，可使用 make court-run"

    fix_hints = [
        "hermes profile create court-team",
        "hermes profile create court-verify",
        "hermes profile create court-synthesize",
        f"hermes skills install {ROOT / 'scripts/skills/harness-court-team'}",
    ]

    return {
        "level": level,
        "summary": summary,
        "checks": checks,
        "fix_hints": fix_hints,
        "hermes_path": str(hermes_path) if hermes_path.is_file() else HERMES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hermes readiness doctor")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true", help="Exit 0 if logic only")
    args = parser.parse_args()

    if args.check:
        data = run_check()
        assert "level" in data and "summary" in data
        print("hermes_doctor --check passed")
        return 0

    data = run_check()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data["summary"])
        for c in data["checks"]:
            mark = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}[c["status"]]
            print(f"  [{mark}] {c['id']}: {c['detail']}")
        if data["level"] != "ok":
            print("\n修复建议:")
            for hint in data["fix_hints"]:
                print(f"  {hint}")
    return 0 if data["level"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
