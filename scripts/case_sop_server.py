#!/usr/bin/env python3
"""Harness Web Hub: patch cases, serve dashboards (127.0.0.1 only)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    AUTH_FIELDS,
    DECISION_PATCHABLE,
    INTAKE_PATCHABLE,
    ROOT,
    append_debate_minute,
    get_wizard_state,
    resolve_case_dir,
    validate_authorization_patch,
    write_frontmatter,
)
from lib.hub_api import (  # noqa: E402
    consume_qq_auth_token,
    create_qq_auth_pending,
    list_cases,
    read_case_file,
    run_court_dispatch,
    run_court_launch,
    run_fork_case,
    run_hermes_doctor,
    run_new_case,
    start_court_dispatch_job,
    start_workflow_job,
)
from lib.hub_jobs import get_job  # noqa: E402
from lib.hub_page import render_hub_page  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765
PIDFILE = ROOT / "artifacts" / ".sop_server.pid"
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    for key, value in CORS_HEADERS.items():
        handler.send_header(key, value)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler: BaseHTTPRequestHandler, status: int, content: str) -> None:
    body = content.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


def case_path_from_query(handler: BaseHTTPRequestHandler) -> Path:
    qs = parse_qs(urlparse(handler.path).query)
    raw = (qs.get("path") or [""])[0]
    if not raw:
        raise ValueError("missing path query")
    return resolve_case_dir(ROOT / raw)


def patch_case(
    case_dir: Path,
    target: str,
    fields: dict[str, Any],
    debate_minute: str | None,
    owner_confirmed: bool,
) -> dict[str, Any]:
    intake_path = case_dir / "01_case_intake.md"
    decision_path = case_dir / "07_orchestrator_decision.md"

    if target == "intake":
        allowed = INTAKE_PATCHABLE
        rel = "01_case_intake.md"
    elif target == "decision":
        allowed = DECISION_PATCHABLE
        rel = "07_orchestrator_decision.md"
    else:
        raise ValueError("target must be intake or decision")

    unknown = set(fields) - allowed
    if unknown:
        raise ValueError(f"fields not allowed: {sorted(unknown)}")

    auth_patch = {k: v for k, v in fields.items() if k in AUTH_FIELDS}
    if auth_patch:
        from lib.case_chain import parse_frontmatter  # noqa: PLC0415

        intake = parse_frontmatter(intake_path)
        decision = parse_frontmatter(decision_path) if decision_path.is_file() else {}
        err = validate_authorization_patch(intake, decision, auth_patch, owner_confirmed)
        if err:
            raise PermissionError(err)

    path = case_dir / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    write_frontmatter(path, fields)
    if debate_minute:
        append_debate_minute(case_dir, debate_minute)
    return get_wizard_state(case_dir)


def authorize_case(case_dir: Path, fields: dict[str, Any], owner_confirmed: bool) -> dict[str, Any]:
    if not owner_confirmed:
        raise PermissionError("authorize 需要 owner_confirmed: true")
    patch = {k: v for k, v in fields.items() if k in AUTH_FIELDS}
    if not patch:
        raise ValueError("no auth fields in body")
    from lib.case_chain import parse_frontmatter  # noqa: PLC0415

    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    err = validate_authorization_patch(intake, decision, patch, owner_confirmed=True)
    if err:
        raise PermissionError(err)
    for rel in ("01_case_intake.md", "07_orchestrator_decision.md"):
        path = case_dir / rel
        if path.is_file():
            write_frontmatter(path, patch)
    return get_wizard_state(case_dir)


def regenerate_dashboard(case_dir: Path) -> str:
    script = ROOT / "scripts" / "render_case_dashboard.py"
    subprocess.run(
        [sys.executable, str(script), str(case_dir.relative_to(ROOT)), "--force"],
        cwd=ROOT,
        check=True,
    )
    return str(case_dir / "artifacts" / "CASE_DASHBOARD.html")


def render_served_dashboard(case_dir: Path) -> str:
    from render_case_dashboard import render_case_html  # noqa: PLC0415

    return render_case_html(case_dir, hub_mode=True)


class SopHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path in {"/", "/hub"}:
                html_response(self, 200, render_hub_page(list_cases()))
                return
            if parsed.path == "/case":
                case_dir = case_path_from_query(self)
                html_response(self, 200, render_served_dashboard(case_dir))
                return
            if parsed.path == "/api/cases":
                json_response(self, 200, {"cases": list_cases()})
                return
            if parsed.path == "/api/case":
                case_dir = case_path_from_query(self)
                json_response(self, 200, get_wizard_state(case_dir))
                return
            if parsed.path == "/api/hermes/doctor":
                json_response(self, 200, run_hermes_doctor())
                return
            if parsed.path == "/api/raw":
                case_dir = case_path_from_query(self)
                qs = parse_qs(parsed.query)
                rel_file = (qs.get("file") or [""])[0]
                ctype, body = read_case_file(case_dir, rel_file)
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if parsed.path.startswith("/api/jobs/"):
                job_id = parsed.path.split("/api/jobs/", 1)[-1]
                job = get_job(job_id)
                if not job:
                    json_response(self, 404, {"error": "job not found"})
                    return
                json_response(self, 200, job)
                return
            if parsed.path == "/health":
                json_response(self, 200, {"ok": True, "hub": True})
                return
            json_response(self, 404, {"error": "not found"})
        except ValueError as exc:
            json_response(self, 400, {"error": str(exc)})
        except PermissionError as exc:
            json_response(self, 403, {"error": str(exc)})
        except FileNotFoundError as exc:
            json_response(self, 404, {"error": str(exc)})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            body = read_json(self)
            case_dir = None
            if body.get("path"):
                case_dir = resolve_case_dir(ROOT / body["path"])

            if parsed.path == "/api/start":
                result = run_new_case(
                    topic=str(body.get("topic", "")).strip(),
                    case_type=str(body.get("case_type", "career_direction")),
                    risk_tier=str(body.get("risk_tier", "high")),
                    needs_execution=bool(body.get("needs_execution")),
                    slug=body.get("slug"),
                )
                json_response(self, 200, result)
                return

            if parsed.path == "/api/fork":
                result = run_fork_case(
                    source_path=str(body.get("from", "")),
                    slug=body.get("slug"),
                    case_type=body.get("case_type"),
                    risk_tier=body.get("risk_tier"),
                    needs_execution=bool(body.get("needs_execution")),
                )
                json_response(self, 200, result)
                return

            if parsed.path == "/api/patch":
                assert case_dir is not None
                state = patch_case(
                    case_dir,
                    str(body.get("target", "intake")),
                    dict(body.get("fields") or {}),
                    body.get("debate_minute"),
                    bool(body.get("owner_confirmed")),
                )
                json_response(self, 200, state)
                return

            if parsed.path == "/api/authorize":
                assert case_dir is not None
                token = body.get("qq_token")
                if token:
                    pending = consume_qq_auth_token(case_dir, str(token))
                    body_fields = pending["fields"]
                    owner_confirmed = True
                else:
                    body_fields = dict(body.get("fields") or {})
                    owner_confirmed = bool(body.get("owner_confirmed"))
                state = authorize_case(case_dir, body_fields, owner_confirmed)
                json_response(self, 200, state)
                return

            if parsed.path == "/api/qq/authorize-request":
                assert case_dir is not None
                pending = create_qq_auth_pending(
                    case_dir, str(body.get("authorized_phase", "phase1"))
                )
                json_response(self, 200, pending)
                return

            if parsed.path == "/api/qq/confirm":
                assert case_dir is not None
                pending = consume_qq_auth_token(case_dir, str(body.get("token", "")))
                state = authorize_case(case_dir, pending["fields"], owner_confirmed=True)
                json_response(self, 200, {"authorized": True, "wizard": state})
                return

            if parsed.path == "/api/regenerate":
                assert case_dir is not None
                out = regenerate_dashboard(case_dir)
                json_response(
                    self, 200, {"dashboard": out, "wizard": get_wizard_state(case_dir)}
                )
                return

            if parsed.path == "/api/court-launch":
                assert case_dir is not None
                json_response(self, 200, run_court_launch(case_dir))
                return

            if parsed.path == "/api/court-dispatch":
                assert case_dir is not None
                doctor = run_hermes_doctor()
                if doctor.get("level") == "bad":
                    json_response(
                        self,
                        400,
                        {"error": doctor.get("summary"), "doctor": doctor},
                    )
                    return
                job_id = start_court_dispatch_job(case_dir)
                json_response(self, 200, {"job_id": job_id, "doctor": doctor})
                return

            if parsed.path == "/api/workflow/tick":
                assert case_dir is not None
                job_id = start_workflow_job(case_dir)
                json_response(self, 200, {"job_id": job_id})
                return

            json_response(self, 404, {"error": "not found"})
        except PermissionError as exc:
            json_response(self, 403, {"error": str(exc)})
        except (ValueError, FileNotFoundError) as exc:
            json_response(self, 400, {"error": str(exc)})
        except subprocess.CalledProcessError as exc:
            json_response(self, 500, {"error": f"command failed: {exc}"})


def run_check() -> int:
    """API logic smoke without binding a port."""
    sample = ROOT / "cases/samples/CASE-001-mems-career-direction"
    state = get_wizard_state(sample)
    assert state.get("case_id"), "wizard state missing case_id"

    try:
        resolve_case_dir(ROOT / "README.md")
        print("ERROR: resolve_case_dir should reject README.md")
        return 1
    except ValueError:
        pass

    cases = list_cases()
    assert isinstance(cases, list), "list_cases must return list"
    assert any(c.get("case_id") for c in cases), "list_cases empty"

    from render_case_dashboard import render_case_html  # noqa: PLC0415

    html = render_case_html(sample, hub_mode=True)
    assert "panel-owner-next" in html, "hub dashboard missing owner-next"
    assert 'const SOP_API = ""' in html or "const SOP_API = ''" in html, "hub SOP_API"

    doctor = run_hermes_doctor()
    assert "level" in doctor

    from lib.case_chain import parse_frontmatter  # noqa: PLC0415

    intake = parse_frontmatter(sample / "01_case_intake.md")
    decision = parse_frontmatter(sample / "07_orchestrator_decision.md")
    err = validate_authorization_patch(
        intake, decision, {"execution_authorized": True}, owner_confirmed=False
    )
    if err is None:
        print("ERROR: expected auth rejection without owner_confirmed")
        return 1

    pending = create_qq_auth_pending(sample, "phase1")
    assert pending.get("token")
    consumed = consume_qq_auth_token(sample, pending["token"])
    assert consumed["fields"]["execution_authorized"] is True

    print("case_sop_server --check passed (hub)")
    return 0


def write_pidfile(port: int) -> None:
    PIDFILE.parent.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(f"{port}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness Web Hub HTTP server")
    parser.add_argument("--check", action="store_true", help="Run API checks without server")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    if args.check:
        return run_check()

    write_pidfile(args.port)
    server = ThreadingHTTPServer((HOST, args.port), SopHandler)
    print(f"Harness Web Hub http://{HOST}:{args.port}/")
    print(f"Cases under {ROOT / 'cases'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
