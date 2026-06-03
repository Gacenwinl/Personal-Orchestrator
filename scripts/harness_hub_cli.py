#!/usr/bin/env python3
"""CLI for Harness Web Hub API (used by harness-owner skill / QQ bridge)."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8765"


def request(
    method: str, path: str, body: dict | None = None, base: str = DEFAULT_BASE
) -> dict:
    url = base.rstrip("/") + path
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": raw or exc.reason}
        raise SystemExit(f"HTTP {exc.code}: {payload.get('error', raw)}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Hub 未运行: {base} — 请先 make hub\n{exc}"
        ) from exc


def cmd_cases(args: argparse.Namespace) -> int:
    data = request("GET", "/api/cases", base=args.base)
    lines = []
    for row in data.get("cases", []):
        lines.append(
            f"{row.get('lifecycle_label', row.get('lifecycle'))} | "
            f"{row.get('case_id')} | {row.get('status')} | {row.get('case_dir')}"
        )
    print("\n".join(lines) if lines else "(无案件)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = args.case if args.case.startswith("cases/") else f"cases/active/{args.case}"
    data = request("GET", f"/api/case?path={urllib.parse.quote(path, safe='/')}", base=args.base)
    lc = data.get("lifecycle") or {}
    print(lc.get("headline") or data.get("next_action", ""))
    for item in lc.get("owner_actions") or []:
        print(f"- {item.get('title', '')}")
    print(f"dashboard: /case?path={path}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    data = request("GET", "/api/hermes/doctor", base=args.base)
    print(data.get("summary", ""))
    for check in data.get("checks", []):
        print(f"  [{check.get('status')}] {check.get('id')}: {check.get('detail')}")
    return 0 if data.get("level") == "ok" else 1


def cmd_authorize_request(args: argparse.Namespace) -> int:
    path = args.case if args.case.startswith("cases/") else f"cases/active/{args.case}"
    data = request(
        "POST",
        "/api/qq/authorize-request",
        {"path": path, "authorized_phase": args.phase},
        base=args.base,
    )
    print(data.get("message", ""))
    print(f"token: {data.get('token')}")
    return 0


def cmd_confirm(args: argparse.Namespace) -> int:
    path = args.case if args.case.startswith("cases/") else f"cases/active/{args.case}"
    data = request(
        "POST",
        "/api/qq/confirm",
        {"path": path, "token": args.token},
        base=args.base,
    )
    print("authorized OK")
    print(json.dumps(data.get("wizard", {}).get("auth", {}), ensure_ascii=False))
    return 0


def cmd_court(args: argparse.Namespace) -> int:
    path = args.case if args.case.startswith("cases/") else f"cases/active/{args.case}"
    data = request("POST", "/api/court-dispatch", {"path": path}, base=args.base)
    if data.get("job_id"):
        print(f"job_id: {data['job_id']}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness Hub CLI")
    parser.add_argument("--base", default=DEFAULT_BASE)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cases = sub.add_parser("cases", help="List cases")
    p_cases.set_defaults(func=cmd_cases)

    p_status = sub.add_parser("status", help="Case status")
    p_status.add_argument("case", help="case_dir or case_id")
    p_status.set_defaults(func=cmd_status)

    p_doc = sub.add_parser("doctor", help="Hermes doctor")
    p_doc.set_defaults(func=cmd_doctor)

    p_auth = sub.add_parser("authorize-request", help="QQ auth token")
    p_auth.add_argument("case")
    p_auth.add_argument("--phase", default="phase1")
    p_auth.set_defaults(func=cmd_authorize_request)

    p_conf = sub.add_parser("confirm", help="Confirm QQ auth")
    p_conf.add_argument("case")
    p_conf.add_argument("token")
    p_conf.set_defaults(func=cmd_confirm)

    p_court = sub.add_parser("court-dispatch", help="Run court dispatch")
    p_court.add_argument("case")
    p_court.set_defaults(func=cmd_court)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
