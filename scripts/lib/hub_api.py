"""Harness Web Hub API helpers (used by case_sop_server)."""

from __future__ import annotations

import json
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.case_chain import ROOT, derive_owner_lifecycle, parse_frontmatter, resolve_case_dir
from lib.dashboard_owner import LIFECYCLE_LABELS
from lib.hub_jobs import create_job, run_in_background, run_subprocess_job, run_workflow_tick

CASE_ROOTS = [ROOT / "cases" / "active", ROOT / "cases" / "samples"]
QQ_PENDING = "qq_auth_pending.json"


def list_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in CASE_ROOTS:
        if not root.is_dir():
            continue
        for case_dir in sorted(root.iterdir()):
            if not case_dir.is_dir() or case_dir.name.startswith("."):
                continue
            intake = parse_frontmatter(case_dir / "01_case_intake.md")
            decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
            lc = derive_owner_lifecycle(case_dir)
            rel = str(case_dir.relative_to(ROOT))
            rows.append(
                {
                    "bucket": root.name,
                    "case_id": str(intake.get("case_id", case_dir.name)),
                    "case_dir": rel,
                    "status": str(intake.get("status", "—")),
                    "topic": str(intake.get("topic", ""))[:120],
                    "lifecycle": lc.get("lifecycle", ""),
                    "lifecycle_label": LIFECYCLE_LABELS.get(lc.get("lifecycle", ""), ""),
                    "mtime": lc.get("mtime", ""),
                    "needs_execution": decision.get(
                        "needs_execution", intake.get("needs_execution")
                    ),
                    "execution_authorized": decision.get(
                        "execution_authorized", intake.get("execution_authorized")
                    ),
                    "dashboard_url": f"/case?path={rel}",
                }
            )
    return rows


def run_new_case(
    topic: str,
    case_type: str = "career_direction",
    risk_tier: str = "high",
    needs_execution: bool = False,
    slug: str | None = None,
) -> dict[str, Any]:
    from new_case import create_case  # noqa: PLC0415

    case_dir = create_case(
        topic=topic,
        case_type=case_type,
        risk_tier=risk_tier,
        needs_execution=needs_execution,
        cases_root=ROOT / "cases" / "active",
        slug=slug,
    )
    rel = str(case_dir.relative_to(ROOT))
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/render_case_dashboard.py"), rel, "--force"],
        cwd=ROOT,
        check=True,
    )
    return {
        "case_dir": rel,
        "case_id": case_dir.name,
        "dashboard_url": f"/case?path={rel}",
        "lifecycle": derive_owner_lifecycle(case_dir),
    }


def run_fork_case(
    source_path: str,
    slug: str | None = None,
    case_type: str | None = None,
    risk_tier: str | None = None,
    needs_execution: bool = False,
) -> dict[str, Any]:
    source = resolve_case_dir(ROOT / source_path)
    from fork_case import extract_topic_from_intent  # noqa: PLC0415

    topic = extract_topic_from_intent(source)
    intake_fm: dict[str, str] = {}
    intake_path = source / "01_case_intake.md"
    if intake_path.is_file():
        for line in intake_path.read_text(encoding="utf-8").splitlines():
            if ":" in line and not line.startswith("#"):
                k, v = line.split(":", 1)
                intake_fm[k.strip()] = v.strip()

    return run_new_case(
        topic=topic,
        case_type=case_type or intake_fm.get("case_type", "career_direction"),
        risk_tier=risk_tier or intake_fm.get("risk_tier", "high"),
        needs_execution=needs_execution or intake_fm.get("needs_execution") == "true",
        slug=slug or f"fork-{source.name[-16:]}",
    )


def run_hermes_doctor() -> dict[str, Any]:
    from hermes_doctor import run_check  # noqa: PLC0415

    return run_check()


def run_court_launch(case_dir: Path) -> dict[str, Any]:
    rel = str(case_dir.relative_to(ROOT))
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/court_launcher.py"), rel, "--force"],
        cwd=ROOT,
        check=True,
    )
    plan = case_dir / "artifacts" / "COURT_LAUNCH_PLAN.md"
    return {"plan": str(plan.relative_to(ROOT)), "case_dir": rel}


def run_court_dispatch(case_dir: Path) -> dict[str, Any]:
    rel = str(case_dir.relative_to(ROOT))
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/court_dispatch.py"), rel],
        cwd=ROOT,
        check=True,
    )
    out = case_dir / "artifacts" / "court_dispatch.json"
    payload = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else {}
    return {"dispatch": str(out.relative_to(ROOT)), "teams": payload.get("teams", [])}


def start_workflow_job(case_dir: Path) -> str:
    job_id = create_job("workflow_tick")

    def fn() -> dict[str, Any]:
        return run_workflow_tick(case_dir)

    run_in_background(job_id, fn)
    return job_id


def start_court_dispatch_job(case_dir: Path) -> str:
    job_id = create_job("court_dispatch")
    rel = str(case_dir.relative_to(ROOT))

    def fn() -> dict[str, Any]:
        return run_court_dispatch(case_dir)

    run_in_background(job_id, fn)
    return job_id


def read_case_file(case_dir: Path, rel_file: str) -> tuple[str, bytes]:
    base = case_dir.resolve()
    target = (base / rel_file).resolve()
    if not target.is_file():
        raise FileNotFoundError(rel_file)
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise PermissionError("path outside case") from exc
    if target.suffix.lower() not in {".md", ".json", ".txt", ".log"}:
        raise PermissionError("file type not allowed")
    text = target.read_text(encoding="utf-8")
    return "text/plain; charset=utf-8", text.encode("utf-8")


def create_qq_auth_pending(case_dir: Path, authorized_phase: str = "phase1") -> dict[str, Any]:
    token = secrets.token_hex(4)
    path = case_dir / "artifacts" / QQ_PENDING
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "token": token,
        "authorized_phase": authorized_phase,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "case_dir": str(case_dir.relative_to(ROOT)),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "token": token,
        "case_dir": payload["case_dir"],
        "message": f"回复 confirm {token} 完成授权",
        "pending_file": str(path.relative_to(ROOT)),
    }


def consume_qq_auth_token(case_dir: Path, token: str) -> dict[str, Any]:
    path = case_dir / "artifacts" / QQ_PENDING
    if not path.is_file():
        raise FileNotFoundError("no pending qq auth")
    pending = json.loads(path.read_text(encoding="utf-8"))
    if pending.get("token") != token.strip():
        raise PermissionError("invalid confirm token")
    phase = pending.get("authorized_phase") or "phase1"
    path.unlink(missing_ok=True)
    return {
        "authorized_phase": phase,
        "fields": {
            "needs_execution": True,
            "execution_authorized": True,
            "authorized_phase": phase,
            "human_approval_required": False,
        },
    }
