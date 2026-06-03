"""Shared case audit-chain logic for status, dashboard, and SOP server."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

BASE_CHAIN = [
    ("owner_intent", "00_owner_intent.md", "原始意图"),
    ("case_intake", "01_case_intake.md", "案件定义"),
    ("team_selection", "02_team_selection.md", "团队选择理由"),
    ("mode_selection", "02b_mode_selection.md", "模式选择理由"),
    ("debate_session", "03_debate_session.md", "辩论记录"),
    ("court_summary", "05_court_summary.md", "汇总 verdict"),
    ("cac", "06_critical_assumption_check.md", "关键前提检查"),
    ("decision", "07_orchestrator_decision.md", "Orchestrator 决策"),
    ("phase_plan", "08_phase_plan.md", "Phase 规划"),
    ("instruction", "09_executor_instruction.md", "执行任务书"),
    ("feedback", "10_execution_feedback.md", "执行反馈"),
    ("acceptance", "11_acceptance_review.md", "验收结果"),
    ("lesson", "12_lesson_proposal.md", "lesson proposal"),
]

RECOMMENDED_PLUS = {
    "RECOMMENDED_WITH_MODIFICATIONS",
    "RECOMMENDED",
    "IMMEDIATELY_RECOMMENDED",
}

AUTH_FIELDS = {
    "needs_execution",
    "execution_authorized",
    "authorized_phase",
    "human_approval_required",
}

INTAKE_PATCHABLE = {"status", "court_verdict_tier", "case_type", "risk_tier", "topic"} | AUTH_FIELDS
DECISION_PATCHABLE = AUTH_FIELDS | {"decision"}


def strip_inline_comment(value: str) -> str:
    in_quote: str | None = None
    for index, char in enumerate(value):
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
        elif char == "#" and in_quote is None:
            return value[:index]
    return value


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"", "null", "None", "~"}:
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def serialize_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        if any(ch in value for ch in ':"{}\n#'):
            return json_escape_string(value)
        return value
    return str(value)


def json_escape_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    data: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = parse_scalar(strip_inline_comment(value).strip())
    return data


def read_file_parts(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}, text
    fm: dict[str, Any] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = parse_scalar(strip_inline_comment(value).strip())
    return fm, text[match.end() :]


def write_frontmatter(path: Path, updates: dict[str, Any], backup: bool = True) -> None:
    fm, body = read_file_parts(path)
    fm.update(updates)
    if backup and path.is_file():
        bak = path.parent / "artifacts" / f"{path.name}.bak"
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, bak)
    lines = ["---"]
    for key, value in fm.items():
        lines.append(f"{key}: {serialize_scalar(value)}")
    lines.append("---")
    lines.append("")
    path.write_text("\n".join(lines) + body.lstrip("\n"), encoding="utf-8")


def bool_value(value: Any) -> bool:
    return value is True


def required_chain(
    case_dir: Path, intake: dict[str, Any], decision: dict[str, Any]
) -> list[tuple[str, str, str]]:
    chain = BASE_CHAIN.copy()
    needs_execution = bool_value(decision.get("needs_execution", intake.get("needs_execution")))
    authorized = bool_value(
        decision.get("execution_authorized", intake.get("execution_authorized"))
    )
    risk = intake.get("risk_tier")
    verdict = intake.get("court_verdict_tier")
    cac_required = risk in {"high", "critical"} or verdict in RECOMMENDED_PLUS

    if not cac_required:
        chain = [item for item in chain if item[0] != "cac"]
    if not needs_execution or not authorized:
        chain = [
            item
            for item in chain
            if item[0]
            not in {"phase_plan", "instruction", "feedback", "acceptance"}
        ]
    return chain


def chain_progress(case_dir: Path) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]], dict[str, Any], dict[str, Any]]:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    chain = required_chain(case_dir, intake, decision)
    missing = [item for item in chain if not (case_dir / item[1]).is_file()]
    present = [item for item in chain if (case_dir / item[1]).is_file()]
    return present, missing, intake, decision


def next_action_text(
    missing: list[tuple[str, str, str]], intake: dict[str, Any], decision: dict[str, Any]
) -> str:
    if not missing:
        return "运行 `python3 scripts/validate_case.py <case_dir>`；通过后可考虑 completed。"

    key = missing[0][0]
    if key == "team_selection":
        return "运行 `python3 scripts/suggest_teams.py <case_dir> --write`，再人工补充理由。"
    if key == "mode_selection":
        return "运行 `python3 scripts/suggest_modes.py <case_dir> --write`，再人工补充时间成本与模型分配。"
    if key == "instruction":
        authorized = bool_value(
            decision.get("execution_authorized", intake.get("execution_authorized"))
        )
        if not authorized:
            return "先在 `07_orchestrator_decision.md` 明确授权四字段，不要写可执行任务书。"
        return "填写 `09_executor_instruction.md`，确保包含禁止事项、验收标准、停止条件。"
    if key == "cac":
        return "填写 `06_critical_assumption_check.md`，列出事实/推断/未知与翻转条件。"
    return f"补齐 `{missing[0][1]}`。"


def load_wizard_registry() -> dict[str, Any]:
    path = ROOT / "registry" / "sop_wizard_steps.yaml"
    if not path.is_file():
        return {"steps": {}}
    try:
        import yaml  # noqa: optional
    except ImportError:
        return _load_wizard_registry_minimal(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"steps": {}}


def _load_wizard_registry_minimal(path: Path) -> dict[str, Any]:
    """Parse steps + court_invoke_template without PyYAML."""
    text = path.read_text(encoding="utf-8")
    result: dict[str, Any] = {"steps": {}}
    in_steps = False
    in_court = False
    court_lines: list[str] = []
    current: str | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "steps:":
            in_steps = True
            in_court = False
            current = None
            continue
        if stripped.startswith("court_invoke_template:"):
            in_court = True
            in_steps = False
            current = None
            if "|" not in stripped:
                result["court_invoke_template"] = stripped.split(":", 1)[1].strip().strip('"')
            continue
        if in_court:
            if line and not line[0].isspace() and stripped.endswith(":"):
                in_court = False
            else:
                court_lines.append(line[2:] if line.startswith("  ") else line)
            continue
        if not in_steps:
            continue
        step_match = re.match(r"^  ([a-z_0-9]+):\s*$", line)
        if step_match:
            current = step_match.group(1)
            result["steps"][current] = {}
            continue
        if current and "cursor_prompt:" in line:
            val = line.split("cursor_prompt:", 1)[1].strip().strip('"')
            result["steps"][current]["cursor_prompt"] = val
        elif current and "cli_hint:" in line:
            val = line.split("cli_hint:", 1)[1].strip().strip('"')
            result["steps"][current]["cli_hint"] = val

    if court_lines:
        result["court_invoke_template"] = "\n".join(court_lines).strip()
    return result


def cursor_prompt_for_step(step_key: str, case_dir: Path, rel_file: str) -> str:
    reg = load_wizard_registry()
    step_cfg = (reg.get("steps") or {}).get(step_key) or {}
    template = step_cfg.get("cursor_prompt") or (
        f"你是 Orchestrator。请处理案件 `{case_dir}`，补齐 `{rel_file}`。"
        "遵守 engine/ORCHESTRATOR_RUNBOOK.md；禁止设置 execution_authorized: true 除非 Owner 已批准。"
    )
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    return (
        template.replace("{case_dir}", str(case_dir))
        .replace("{case_id}", str(intake.get("case_id", case_dir.name)))
        .replace("{file}", rel_file)
    )


def parse_team_ids_from_02(case_dir: Path) -> list[str]:
    path = case_dir / "02_team_selection.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    teams: list[str] = []
    in_selected = False
    for line in text.splitlines():
        if "选用团队" in line:
            in_selected = True
            continue
        if in_selected and line.startswith("## "):
            break
        if in_selected and line.startswith("|") and "team_id" not in line and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0]:
                teams.append(cells[0])
    return teams


def load_court_launch_plan(case_dir: Path) -> list[dict[str, str]]:
    plan = case_dir / "artifacts" / "COURT_LAUNCH_PLAN.md"
    if not plan.is_file():
        return []
    rows: list[dict[str, str]] = []
    for line in plan.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and "team_id" in line:
            continue
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 3:
                rows.append(
                    {
                        "team_id": cells[0],
                        "block_path": cells[1],
                        "status": cells[2] if len(cells) > 2 else "",
                    }
                )
    return rows


def append_debate_minute(case_dir: Path, line: str) -> None:
    path = case_dir / "03_debate_session.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "## 讨论纪要"
    bullet = f"- {line.strip()}\n"
    if marker in text:
        parts = text.split(marker, 1)
        text = parts[0] + marker + "\n\n" + bullet + parts[1].lstrip()
    else:
        text = text.rstrip() + "\n\n## 讨论纪要\n\n" + bullet
    path.write_text(text, encoding="utf-8")


def validate_authorization_patch(
    intake: dict[str, Any],
    decision: dict[str, Any],
    patch: dict[str, Any],
    owner_confirmed: bool,
) -> str | None:
    """Return error message or None if ok."""
    exec_auth = patch.get("execution_authorized", decision.get("execution_authorized"))
    human_gate = patch.get("human_approval_required", decision.get("human_approval_required"))
    if bool_value(exec_auth) and bool_value(human_gate):
        return "execution_authorized:true 与 human_approval_required:true 不能同时为真"
    if bool_value(exec_auth) and not owner_confirmed:
        return "设置 execution_authorized:true 需要 Owner 确认（owner_confirmed）"
    phase = patch.get("authorized_phase", decision.get("authorized_phase"))
    if bool_value(exec_auth) and (phase is None or phase == "null"):
        return "execution_authorized:true 需要 authorized_phase"
    return None


def resolve_case_dir(path: Path) -> Path:
    resolved = path.resolve()
    cases_root = (ROOT / "cases").resolve()
    if cases_root not in resolved.parents and resolved != cases_root:
        raise ValueError(f"path must be under {cases_root}")
    return resolved


def get_wizard_state(case_dir: Path) -> dict[str, Any]:
    case_dir = case_dir.resolve()
    present, missing, intake, decision = chain_progress(case_dir)
    current = missing[0] if missing else None
    step_key = current[0] if current else "complete"
    rel_file = current[1] if current else ""
    return {
        "case_dir": str(case_dir.relative_to(ROOT)),
        "case_dir_abs": str(case_dir),
        "case_id": intake.get("case_id", case_dir.name),
        "status": intake.get("status"),
        "topic": intake.get("topic"),
        "auth": {
            "needs_execution": decision.get("needs_execution", intake.get("needs_execution")),
            "execution_authorized": decision.get(
                "execution_authorized", intake.get("execution_authorized")
            ),
            "authorized_phase": decision.get("authorized_phase", intake.get("authorized_phase")),
            "human_approval_required": decision.get(
                "human_approval_required", intake.get("human_approval_required")
            ),
        },
        "present": [{"key": k, "file": r, "label": lb} for k, r, lb in present],
        "missing": [{"key": k, "file": r, "label": lb} for k, r, lb in missing],
        "current_step": {
            "key": step_key,
            "file": rel_file,
            "label": current[2] if current else "链路完整",
        },
        "next_action": next_action_text(missing, intake, decision),
        "cursor_prompt": cursor_prompt_for_step(step_key, case_dir, rel_file),
        "court_teams": parse_team_ids_from_02(case_dir),
        "court_plan": load_court_launch_plan(case_dir),
    }
