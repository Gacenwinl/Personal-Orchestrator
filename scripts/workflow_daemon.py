#!/usr/bin/env python3
"""Six-stage workflow daemon for Personal-Orchestrator-Harness.

Polls case state and auto-advances through stages, blocking at the
Phase A→B authorization gate until the Owner sets execution_authorized=true.

Usage:
    python3 scripts/workflow_daemon.py --case cases/active/CASE-xxx
    make workflow CASE=cases/active/CASE-xxx

Stages:
    Stage 1: 00+01+02+02b+03 ready → dispatch court swarm
    Stage 2: team_blocks written → wait for 05_court_summary
    [GATE] Phase A→B: wait for execution_authorized=true
    Stage 3: send work order to Hermes
    Stage 4: 10 received → optional meta_review if under-delivery
    Stage 5: 11 acceptance done → cross_team_conflict check
    Stage 6: Stage 5 P0 found → update 09 and re-dispatch
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    ROOT,
    bool_value,
    chain_progress,
    parse_frontmatter,
    parse_team_ids_from_02,
)

HERMES = shutil.which("hermes") or str(
    Path.home() / "OpenClaw_Workspace/hermes/venv/bin/hermes"
)
POLL_INTERVAL = 30  # seconds


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str, case_dir: Path | None = None) -> None:
    line = f"[{now_iso()}] {msg}"
    print(line, flush=True)
    if case_dir:
        log_path = case_dir / "artifacts" / "daemon.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def write_error(case_dir: Path, exc: BaseException) -> None:
    path = case_dir / "artifacts" / "daemon_error.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"[{now_iso()}] FATAL\n{traceback.format_exc()}\n", encoding="utf-8"
    )
    print(f"Error written to {path}", flush=True)


class Stage:
    WAITING_PREREQS = "waiting_prereqs"
    COURT_DISPATCHED = "court_dispatched"
    COURT_DONE = "court_done"
    AUTH_GATE = "auth_gate"
    EXECUTION_SENT = "execution_sent"
    FEEDBACK_RECEIVED = "feedback_received"
    ACCEPTANCE_DONE = "acceptance_done"
    GLOBAL_EVAL = "global_eval"
    IMPROVEMENT = "improvement"
    COMPLETE = "complete"


def read_state(case_dir: Path) -> dict:
    p = case_dir / "artifacts" / "daemon_state.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"stage": Stage.WAITING_PREREQS, "history": []}


def write_state(case_dir: Path, state: dict) -> None:
    p = case_dir / "artifacts" / "daemon_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def transition(state: dict, new_stage: str, note: str = "") -> dict:
    state["history"].append({
        "from": state["stage"],
        "to": new_stage,
        "at": now_iso(),
        "note": note,
    })
    state["stage"] = new_stage
    return state


def prereqs_ready(case_dir: Path) -> bool:
    """Stage 1 gate: 00+01+02+02b+03 must all exist."""
    needed = [
        "00_owner_intent.md",
        "01_case_intake.md",
        "02_team_selection.md",
        "02b_mode_selection.md",
        "03_debate_session.md",
    ]
    return all((case_dir / f).is_file() for f in needed)


def court_dispatched(case_dir: Path) -> bool:
    return (case_dir / "artifacts" / "court_dispatch.json").is_file()


def all_team_blocks_present(case_dir: Path) -> bool:
    teams = parse_team_ids_from_02(case_dir)
    if not teams:
        return False
    block_dir = case_dir / "artifacts" / "team_blocks"
    return all((block_dir / f"{t}.md").is_file() for t in teams)


def court_summary_present(case_dir: Path) -> bool:
    return (case_dir / "05_court_summary.md").is_file()


def is_authorized(case_dir: Path) -> bool:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    exec_auth = decision.get("execution_authorized", intake.get("execution_authorized"))
    human_gate = decision.get("human_approval_required", intake.get("human_approval_required"))
    if bool_value(human_gate):
        return False
    return bool_value(exec_auth)


def work_order_sent(case_dir: Path) -> bool:
    return (case_dir / "artifacts" / "work_order_sent.json").is_file()


def feedback_present(case_dir: Path) -> bool:
    return (case_dir / "10_execution_feedback.md").is_file()


def acceptance_present(case_dir: Path) -> bool:
    return (case_dir / "11_acceptance_review.md").is_file()


def lesson_present(case_dir: Path) -> bool:
    return (case_dir / "12_lesson_proposal.md").is_file()


# ---------------------------------------------------------------------------
# Stage actions
# ---------------------------------------------------------------------------

def action_dispatch_court(case_dir: Path, dry_run: bool, case_id: str) -> None:
    script = ROOT / "scripts" / "court_dispatch.py"
    cmd = [sys.executable, str(script), str(case_dir)]
    if dry_run:
        cmd.append("--dry-run")
    log(f"[Stage 1] dispatching court swarm: {' '.join(cmd)}", case_dir)
    subprocess.run(cmd, check=True, cwd=ROOT)


def action_send_work_order(case_dir: Path, dry_run: bool) -> None:
    """Send structured work order to Hermes via `hermes send`."""
    instruction = case_dir / "09_executor_instruction.md"
    if not instruction.is_file():
        log("WARN: 09_executor_instruction.md not found; skipping work order send", case_dir)
        return

    work_order_script = ROOT / "scripts" / "build_work_order.py"
    wo_path = case_dir / "artifacts" / "work_order.json"

    # Build work order JSON
    cmd_build = [sys.executable, str(work_order_script), str(case_dir)]
    log(f"[Stage 3] building work order: {' '.join(cmd_build)}", case_dir)
    if not dry_run:
        subprocess.run(cmd_build, check=True, cwd=ROOT)

    if dry_run:
        log("[Stage 3] dry-run: skipping hermes send", case_dir)
        return

    hermes = HERMES
    if not Path(hermes).is_file():
        log(f"WARN: hermes not found at {hermes}; writing work_order_sent.json as placeholder", case_dir)
        _write_sent_placeholder(case_dir, wo_path)
        return

    # Read work order to get delivery target
    wo = json.loads(wo_path.read_text(encoding="utf-8")) if wo_path.is_file() else {}
    delivery = wo.get("delivery_profile", "default")

    # hermes send --profile <profile> -z <prompt>
    prompt = (
        f"[Harness Executor Instruction] case_id={wo.get('case_id','?')} "
        f"phase={wo.get('phase','?')} "
        f"instruction_path={instruction} "
        f"work_order_path={wo_path}"
    )
    cmd_send = [hermes, "send", "--profile", delivery, "-z", prompt]
    log(f"[Stage 3] hermes send: {' '.join(cmd_send[:5])} ...", case_dir)
    result = subprocess.run(cmd_send, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"WARN: hermes send returned {result.returncode}: {result.stderr[:200]}", case_dir)
    _write_sent_placeholder(case_dir, wo_path, result.returncode)


def _write_sent_placeholder(case_dir: Path, wo_path: Path, rc: int = 0) -> None:
    sentinel = case_dir / "artifacts" / "work_order_sent.json"
    sentinel.write_text(
        json.dumps({"sent_at": now_iso(), "work_order": str(wo_path), "hermes_rc": rc},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"Work order sent record: {sentinel}", case_dir)


def action_meta_review(case_dir: Path) -> None:
    """Stage 4: trigger meta_review if feedback signals under-delivery."""
    feedback = case_dir / "10_execution_feedback.md"
    text = feedback.read_text(encoding="utf-8") if feedback.is_file() else ""
    if "under_delivery" in text.lower() or "未达标" in text:
        log("[Stage 4] under-delivery detected; triggering meta_review swarm", case_dir)
        script = ROOT / "scripts" / "court_dispatch.py"
        subprocess.run(
            [sys.executable, str(script), str(case_dir),
             "--idempotency-key", f"{case_dir.name}-meta"],
            check=False, cwd=ROOT,
        )
    else:
        log("[Stage 4] feedback OK; no meta_review needed", case_dir)


def action_cross_team_eval(case_dir: Path) -> None:
    """Stage 5: check court_summary for unresolved P0 conflicts."""
    summary = case_dir / "05_court_summary.md"
    text = summary.read_text(encoding="utf-8") if summary.is_file() else ""
    p0_count = text.count("P0")
    result_path = case_dir / "artifacts" / "stage5_eval.json"
    result_path.write_text(
        json.dumps({"p0_count": p0_count, "evaluated_at": now_iso()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"[Stage 5] cross-team eval: {p0_count} P0 items found", case_dir)
    if p0_count > 0:
        log("[Stage 5] P0 items exist — Stage 6 improvement required", case_dir)


def action_stage6_improvement(case_dir: Path) -> None:
    """Stage 6: if P0 items found, log guidance for Orchestrator to update 09."""
    eval_path = case_dir / "artifacts" / "stage5_eval.json"
    if not eval_path.is_file():
        return
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    if data.get("p0_count", 0) > 0:
        guide = case_dir / "artifacts" / "stage6_improvement_needed.md"
        guide.write_text(
            f"# Stage 6 Improvement Required\n\n"
            f"Generated: {now_iso()}\n\n"
            f"Stage 5 found {data['p0_count']} P0 item(s) in 05_court_summary.md.\n\n"
            f"**Orchestrator action required:**\n"
            f"1. Review P0 conflicts in `05_court_summary.md`\n"
            f"2. Update `09_executor_instruction.md` with revised approach\n"
            f"3. Re-run `make work-order CASE={case_dir}` and re-send\n",
            encoding="utf-8",
        )
        log(f"[Stage 6] improvement guide written to {guide}", case_dir)
    else:
        log("[Stage 6] no P0 items; workflow complete", case_dir)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_daemon(case_dir: Path, dry_run: bool, once: bool) -> int:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    case_id = intake.get("case_id", case_dir.name)
    log(f"Workflow daemon started for {case_id} (dry_run={dry_run})", case_dir)

    while True:
        try:
            state = read_state(case_dir)
            stage = state["stage"]
            changed = False

            # Stage 1: prereqs check → dispatch court
            if stage == Stage.WAITING_PREREQS:
                if prereqs_ready(case_dir):
                    if not court_dispatched(case_dir):
                        action_dispatch_court(case_dir, dry_run, case_id)
                    state = transition(state, Stage.COURT_DISPATCHED, "prereqs ready")
                    changed = True
                else:
                    log("Stage 1: waiting for 00/01/02/02b/03 …", case_dir)

            # Stage 2: wait for team blocks + court summary
            elif stage == Stage.COURT_DISPATCHED:
                if court_summary_present(case_dir):
                    state = transition(state, Stage.COURT_DONE, "05 written by synthesizer")
                    changed = True
                elif all_team_blocks_present(case_dir):
                    log("Stage 2: all team_blocks present, waiting for synthesizer to write 05 …", case_dir)
                else:
                    log("Stage 2: waiting for team_blocks and 05_court_summary …", case_dir)

            # Authorization gate
            elif stage == Stage.COURT_DONE:
                state = transition(state, Stage.AUTH_GATE, "court complete; waiting for authorization")
                changed = True

            elif stage == Stage.AUTH_GATE:
                if is_authorized(case_dir):
                    log("AUTH GATE: execution_authorized=true detected; proceeding to Stage 3", case_dir)
                    state = transition(state, Stage.EXECUTION_SENT, "authorized")
                    action_send_work_order(case_dir, dry_run)
                    changed = True
                else:
                    log(
                        "AUTH GATE (blocking): set execution_authorized=true in 01 or 07\n"
                        "  Options: make sop-console → 看板向导 → 授权闸门\n"
                        "           或手动编辑 07_orchestrator_decision.md",
                        case_dir,
                    )

            # Stage 3→4: wait for feedback
            elif stage == Stage.EXECUTION_SENT:
                if feedback_present(case_dir):
                    action_meta_review(case_dir)
                    state = transition(state, Stage.FEEDBACK_RECEIVED, "10 present")
                    changed = True
                else:
                    log("Stage 3: waiting for 10_execution_feedback.md …", case_dir)

            # Stage 4→5: wait for acceptance
            elif stage == Stage.FEEDBACK_RECEIVED:
                if acceptance_present(case_dir):
                    action_cross_team_eval(case_dir)
                    state = transition(state, Stage.ACCEPTANCE_DONE, "11 present")
                    changed = True
                else:
                    log("Stage 4: waiting for 11_acceptance_review.md …", case_dir)

            # Stage 5→6
            elif stage == Stage.ACCEPTANCE_DONE:
                action_stage6_improvement(case_dir)
                state = transition(state, Stage.GLOBAL_EVAL, "stage 5 complete")
                changed = True

            # Stage 6: check if done or needs loop
            elif stage == Stage.GLOBAL_EVAL:
                guide = case_dir / "artifacts" / "stage6_improvement_needed.md"
                if guide.is_file():
                    log("Stage 6: improvement guide present; waiting for Orchestrator update …", case_dir)
                elif lesson_present(case_dir):
                    state = transition(state, Stage.COMPLETE, "12 present")
                    changed = True
                else:
                    log("Stage 6: waiting for 12_lesson_proposal.md …", case_dir)

            elif stage == Stage.COMPLETE:
                log(f"Workflow complete for {case_id}. All stages done.", case_dir)
                write_state(case_dir, state)
                return 0

            if changed:
                write_state(case_dir, state)
                log(f"State → {state['stage']}", case_dir)

        except subprocess.CalledProcessError as exc:
            log(f"ERROR: subprocess failed: {exc}", case_dir)
            write_error(case_dir, exc)
            return 1
        except Exception as exc:  # noqa: BLE001
            log(f"FATAL: {exc}", case_dir)
            write_error(case_dir, exc)
            return 1

        if once:
            return 0

        time.sleep(POLL_INTERVAL)


def main() -> int:
    parser = argparse.ArgumentParser(description="Six-stage workflow daemon")
    parser.add_argument("--case", required=True, help="Case directory path")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate actions without calling hermes")
    parser.add_argument("--once", action="store_true",
                        help="Run one tick and exit (for smoke test / CI)")
    parser.add_argument("--check", action="store_true",
                        help="Logic check without running daemon")
    args = parser.parse_args()

    case_dir = Path(args.case).resolve()
    if not case_dir.is_dir():
        print(f"ERROR: case directory not found: {case_dir}")
        return 1

    if args.check:
        # Quick smoke: verify imports + stage logic imports ok
        state = {"stage": Stage.WAITING_PREREQS, "history": []}
        state = transition(state, Stage.COURT_DISPATCHED, "check")
        assert state["stage"] == Stage.COURT_DISPATCHED
        print("workflow_daemon --check passed")
        return 0

    return run_daemon(case_dir, dry_run=args.dry_run, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
