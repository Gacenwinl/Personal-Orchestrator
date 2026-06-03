"""In-memory background job registry for Harness Web Hub."""

from __future__ import annotations

import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class JobRecord:
    job_id: str
    kind: str
    status: str  # pending | running | done | failed
    created_at: str
    message: str = ""
    result: dict[str, Any] = field(default_factory=dict)


_lock = threading.Lock()
_jobs: dict[str, JobRecord] = {}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def create_job(kind: str) -> str:
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = JobRecord(
            job_id=job_id,
            kind=kind,
            status="pending",
            created_at=_now(),
        )
    return job_id


def update_job(job_id: str, **kwargs: Any) -> None:
    with _lock:
        rec = _jobs.get(job_id)
        if not rec:
            return
        for key, value in kwargs.items():
            if hasattr(rec, key):
                setattr(rec, key, value)


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        rec = _jobs.get(job_id)
        if not rec:
            return None
        return {
            "job_id": rec.job_id,
            "kind": rec.kind,
            "status": rec.status,
            "created_at": rec.created_at,
            "message": rec.message,
            "result": rec.result,
        }


def run_in_background(job_id: str, fn: Callable[[], dict[str, Any]]) -> None:
    def worker() -> None:
        update_job(job_id, status="running")
        try:
            result = fn()
            update_job(job_id, status="done", result=result, message="ok")
        except Exception as exc:  # noqa: BLE001
            update_job(job_id, status="failed", message=str(exc))

    threading.Thread(target=worker, daemon=True).start()


def run_subprocess_job(
    job_id: str,
    cmd: list[str],
    cwd: Path | None = None,
    timeout: int = 600,
) -> None:
    def fn() -> dict[str, Any]:
        result = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "failed")
        return {"stdout": result.stdout[-2000:], "returncode": 0}

    run_in_background(job_id, fn)


def run_workflow_tick(case_dir: Path) -> dict[str, Any]:
    script = ROOT / "scripts" / "workflow_daemon.py"
    rel = str(case_dir.relative_to(ROOT))
    result = subprocess.run(
        [sys.executable, str(script), "--case", rel, "--once"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "workflow tick failed")
    return {"stdout": result.stdout[-2000:]}
