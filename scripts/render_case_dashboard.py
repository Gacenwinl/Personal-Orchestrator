#!/usr/bin/env python3
"""Render a self-contained HTML dashboard for a harness case directory."""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.case_chain import (  # noqa: E402
    BASE_CHAIN,
    ROOT,
    chain_progress,
    derive_owner_lifecycle,
    get_wizard_state,
    load_wizard_registry,
    parse_frontmatter,
    required_chain,
    sync_case_todo,
)
from lib.dashboard_owner import (  # noqa: E402
    LIFECYCLE_LABELS,
    OWNER_EXTRA_CSS,
    court_panel_enhanced_html,
    load_automation_artifacts,
    owner_next_panel_html,
    wizard_banner_if_complete,
)
from lib.dashboard_wizard import (  # noqa: E402
    WIZARD_EXTRA_CSS,
    wizard_panel_html,
    wizard_script,
)


def fetch_hermes_status() -> dict[str, Any]:
    script = ROOT / "scripts" / "hermes_doctor.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError):
        pass
    return {"level": "warn", "summary": "Hermes 状态未检测（可运行 make hermes-doctor）"}


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*$(.+?)(?=^##\s+|\Z)"
    match = re.search(pattern, body, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group(1).strip()


def extract_bullets(text: str, limit: int = 12) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        if len(items) >= limit:
            break
    return items


def parse_markdown_tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("|") and index + 1 < len(lines) and re.match(
            r"^\|[-:\s|]+\|$", lines[index + 1].strip()
        ):
            rows: list[list[str]] = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                rows.append(cells)
                index += 1
            if rows:
                tables.append(rows)
            continue
        index += 1
    return tables


def load_team_blocks(case_dir: Path) -> list[dict[str, Any]]:
    block_dir = case_dir / "artifacts" / "team_blocks"
    if not block_dir.is_dir():
        return []
    teams: list[dict[str, Any]] = []
    for path in sorted(block_dir.glob("*.md")):
        fm = parse_frontmatter(path)
        body = path.read_text(encoding="utf-8")
        if body.startswith("---"):
            body = re.sub(r"^---\n.*?\n---\n", "", body, count=1, flags=re.DOTALL)
        teams.append(
            {
                "team_id": fm.get("team_id", path.stem),
                "tier": fm.get("team_verdict_tier", "—"),
                "confidence": fm.get("confidence", "—"),
                "findings": extract_bullets(extract_section(body, "Findings"), 6),
                "conflicts": extract_bullets(extract_section(body, "Conflicts noted"), 4),
                "path": href_from_dashboard(case_dir, path),
            }
        )
    return teams


def load_outputs(case_dir: Path) -> list[dict[str, str]]:
    out_dir = case_dir / "outputs"
    if not out_dir.is_dir():
        return []
    rows: list[dict[str, str]] = []
    for path in sorted(out_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = ""
        for line in text.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        summary = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                summary = stripped[:200]
                break
        rows.append(
            {
                "name": path.name,
                "title": title or path.stem,
                "summary": summary,
                "path": href_from_dashboard(case_dir, path),
            }
        )
    return rows


def href_from_dashboard(case_dir: Path, target: Path) -> str:
    rel = target.relative_to(case_dir)
    parts = rel.parts
    if parts and parts[0] == "artifacts" and len(parts) > 1:
        return Path(*parts[1:]).as_posix()
    return Path("..", *parts).as_posix()


def rel_from_cases_index(case_dir: Path) -> str:
    try:
        rel = case_dir.relative_to(ROOT / "cases")
        return f"{rel.as_posix()}/artifacts/CASE_DASHBOARD.html"
    except ValueError:
        return ""


def build_case_data(case_dir: Path) -> dict[str, Any]:
    intake = parse_frontmatter(case_dir / "01_case_intake.md")
    decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
    chain = required_chain(case_dir, intake, decision)

    steps = []
    for key, rel, label in chain:
        present = (case_dir / rel).is_file()
        steps.append({"key": key, "file": rel, "label": label, "present": present})

    debate_path = case_dir / "03_debate_session.md"
    debate_body = debate_path.read_text(encoding="utf-8") if debate_path.is_file() else ""
    if debate_body.startswith("---"):
        debate_body = re.sub(r"^---\n.*?\n---\n", "", debate_body, count=1, flags=re.DOTALL)

    cac_path = case_dir / "06_critical_assumption_check.md"
    cac_body = cac_path.read_text(encoding="utf-8") if cac_path.is_file() else ""
    if cac_body.startswith("---"):
        cac_body = re.sub(r"^---\n.*?\n---\n", "", cac_body, count=1, flags=re.DOTALL)

    todo_path = case_dir / "CASE_TODO.md"
    todo_text = todo_path.read_text(encoding="utf-8") if todo_path.is_file() else ""

    wizard = get_wizard_state(case_dir)
    lifecycle = wizard.get("lifecycle") or derive_owner_lifecycle(case_dir)
    reg = load_wizard_registry()
    step_cfg = (reg.get("steps") or {}).get(wizard["current_step"]["key"], {})
    wizard["cli_hint"] = step_cfg.get("cli_hint", "")
    automation = load_automation_artifacts(case_dir)
    hermes = fetch_hermes_status()

    _, missing, _, _ = chain_progress(case_dir)

    return {
        "case_id": intake.get("case_id", case_dir.name),
        "case_dir": str(case_dir.relative_to(ROOT)),
        "status": intake.get("status", "—"),
        "topic": intake.get("topic", "—"),
        "case_type": intake.get("case_type", "—"),
        "risk_tier": intake.get("risk_tier", "—"),
        "court_verdict_tier": intake.get("court_verdict_tier", "—"),
        "auth": wizard["auth"],
        "steps": steps,
        "wizard": wizard,
        "lifecycle": lifecycle,
        "automation": automation,
        "hermes": hermes,
        "next_action": wizard["next_action"],
        "debate": {
            "modes": extract_bullets(extract_section(debate_body, "模式执行记录") or debate_body, 8),
            "minutes": extract_bullets(extract_section(debate_body, "讨论纪要"), 20),
            "conflict_tables": parse_markdown_tables(
                extract_section(debate_body, "冲突摘要") or debate_body
            ),
            "focus": extract_section(debate_body, "焦点").splitlines()[0]
            if extract_section(debate_body, "焦点")
            else "",
        },
        "cac_tables": parse_markdown_tables(cac_body),
        "teams": load_team_blocks(case_dir),
        "outputs": load_outputs(case_dir),
        "todo": todo_text[:1500],
        "has_missing": bool(missing),
        "files": [
            {"rel": rel, "label": label, "href": Path("..", rel).as_posix()}
            for _, rel, label in BASE_CHAIN
            if (case_dir / rel).is_file()
        ],
    }


def render_table(rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>—</p>"
    head = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    parts = ["<table><thead><tr>"]
    for cell in head:
        parts.append(f"<th>{html.escape(cell)}</th>")
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>")
        for cell in row:
            parts.append(f"<td>{html.escape(cell)}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def gate_class(value: Any, good_when_true: bool = True) -> str:
    if value is True:
        return "gate-ok" if good_when_true else "gate-warn"
    if value is False:
        return "gate-warn" if good_when_true else "gate-ok"
    return "gate-neutral"


def render_html(data: dict[str, Any]) -> str:
    auth = data["auth"]
    wizard = data.get("wizard") or {}
    steps_html = []
    done = sum(1 for s in data["steps"] if s["present"])
    total = len(data["steps"])
    for step in data["steps"]:
        cls = "step ok" if step["present"] else "step miss"
        mark = "✓" if step["present"] else "○"
        href = html.escape(f"../{step['file']}")
        steps_html.append(
            f'<div class="{cls}"><span class="mark">{mark}</span>'
            f'<a href="{href}">{html.escape(step["label"])}</a>'
            f'<code>{html.escape(step["file"])}</code></div>'
        )

    teams_html = []
    for team in data["teams"]:
        findings = "".join(f"<li>{html.escape(x)}</li>" for x in team["findings"]) or "<li class='muted'>—</li>"
        conflicts = "".join(f"<li>{html.escape(x)}</li>" for x in team["conflicts"]) or "<li class='muted'>—</li>"
        teams_html.append(
            f'<article class="team"><header><h3>{html.escape(team["team_id"])}</h3>'
            f'<span class="pill">{html.escape(str(team["tier"]))}</span></header>'
            f'<p class="muted">confidence: {html.escape(str(team["confidence"]))}</p>'
            f"<h4>Findings</h4><ul>{findings}</ul>"
            f"<h4>Conflicts</h4><ul>{conflicts}</ul></article>"
        )

    debate_conflicts = ""
    for table in data["debate"].get("conflict_tables", []):
        debate_conflicts += render_table(table)

    minutes = data["debate"].get("minutes") or []
    minutes_html = "".join(f"<li>{html.escape(x)}</li>" for x in minutes) or (
        "<li class='muted'>（无讨论纪要 — 见 templates/03）</li>"
    )

    cac_html = ""
    for table in data.get("cac_tables", []):
        cac_html += render_table(table)

    outputs_html = ""
    for out in data.get("outputs", []):
        outputs_html += (
            f'<div class="output"><a href="{html.escape(out["path"])}">'
            f'<strong>{html.escape(out["title"])}</strong></a>'
            f'<p>{html.escape(out["summary"])}</p></div>'
        )

    payload = json.dumps(data, ensure_ascii=False)
    topic = html.escape(str(data.get("topic", "")))
    case_id = html.escape(str(data.get("case_id", "")))
    next_action = html.escape(str(data.get("next_action", "")))
    case_rel = str(data.get("case_dir", ""))

    lifecycle = data.get("lifecycle") or {}
    hermes = data.get("hermes") or {}
    automation = data.get("automation") or {}
    lc_label = LIFECYCLE_LABELS.get(lifecycle.get("lifecycle", ""), "")
    banner = wizard_banner_if_complete(lifecycle)
    wizard_html = wizard_panel_html(wizard, banner=banner)
    owner_html = owner_next_panel_html(lifecycle, hermes)
    court_html = court_panel_enhanced_html(wizard, lifecycle, automation)
    wizard_js = wizard_script(case_rel, wizard, lifecycle)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{case_id} — Harness Dashboard</title>
  <style>
    :root {{
      --bg: #0f1419;
      --surface: #1a2332;
      --border: #2d3a4f;
      --text: #e7ecf3;
      --muted: #8b9cb3;
      --accent: #3d8bfd;
      --ok: #3ecf8e;
      --warn: #e8b339;
      --bad: #f07178;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "SF Pro Text", system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; }}
    header.hero {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 20px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 1.35rem; }}
    .topic {{ color: var(--muted); font-size: 0.95rem; margin-bottom: 16px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .badge {{
      font-size: 0.75rem;
      padding: 4px 10px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: var(--bg);
    }}
    .gates {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin: 20px 0;
    }}
    .gate {{
      padding: 12px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--surface);
      font-size: 0.85rem;
    }}
    .gate-ok {{ border-color: var(--ok); }}
    .gate-warn {{ border-color: var(--warn); }}
    .gate-neutral {{ border-color: var(--border); }}
    .gate strong {{ display: block; margin-bottom: 4px; }}
    section {{
      margin-bottom: 24px;
      padding: 18px 20px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}
    h2 {{ margin: 0 0 14px; font-size: 1.05rem; }}
    .progress {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 12px; }}
    .steps {{ display: grid; gap: 6px; }}
    .step {{
      display: grid;
      grid-template-columns: 24px 1fr auto;
      gap: 10px;
      align-items: center;
      padding: 8px 10px;
      border-radius: 6px;
      background: var(--bg);
      font-size: 0.88rem;
    }}
    .step.ok .mark {{ color: var(--ok); }}
    .step.miss .mark {{ color: var(--warn); }}
    .step a {{ color: var(--accent); text-decoration: none; }}
    .step code {{ color: var(--muted); font-size: 0.75rem; }}
    .teams {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 12px;
    }}
    .team {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    .team header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }}
    .team h3 {{ margin: 0; font-size: 0.95rem; }}
    .pill {{
      font-size: 0.7rem;
      padding: 2px 8px;
      border-radius: 4px;
      border: 1px solid var(--border);
      color: var(--muted);
    }}
    .team h4 {{ margin: 12px 0 6px; font-size: 0.75rem; color: var(--muted); text-transform: uppercase; }}
    .team ul {{ margin: 0; padding-left: 18px; font-size: 0.85rem; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      margin-bottom: 12px;
    }}
    th, td {{
      border: 1px solid var(--border);
      padding: 8px 10px;
      text-align: left;
    }}
    th {{ background: var(--bg); color: var(--muted); }}
    .output {{
      padding: 10px 12px;
      background: var(--bg);
      border-radius: 8px;
      margin-bottom: 8px;
    }}
    .output a {{ color: var(--accent); }}
    .todo {{
      white-space: pre-wrap;
      font-size: 0.85rem;
      background: var(--bg);
      padding: 12px;
      border-radius: 8px;
    }}
    .muted {{ color: var(--muted); }}
    footer {{ margin-top: 24px; font-size: 0.75rem; color: var(--muted); }}
    .callout {{
      border-left: 3px solid var(--accent);
      padding: 10px 14px;
      background: var(--bg);
      border-radius: 0 8px 8px 0;
      margin-bottom: 12px;
      font-size: 0.9rem;
    }}
    {WIZARD_EXTRA_CSS}
    {OWNER_EXTRA_CSS}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <h1>{case_id}</h1>
      <p class="topic">{topic}</p>
      <div class="meta">
        <span class="badge">status: {html.escape(str(data.get("status")))}</span>
        <span class="badge">verdict: {html.escape(str(data.get("court_verdict_tier")))}</span>
        <span class="badge">risk: {html.escape(str(data.get("risk_tier")))}</span>
        <span class="badge">type: {html.escape(str(data.get("case_type")))}</span>
        <span class="badge">阶段: {html.escape(lc_label)}</span>
      </div>
      <div class="gates">
        <div class="gate {gate_class(auth.get("needs_execution"))}">
          <strong>needs_execution</strong>{html.escape(str(auth.get("needs_execution")))}
        </div>
        <div class="gate {gate_class(auth.get("execution_authorized"))}">
          <strong>execution_authorized</strong>{html.escape(str(auth.get("execution_authorized")))}
        </div>
        <div class="gate gate-neutral">
          <strong>authorized_phase</strong>{html.escape(str(auth.get("authorized_phase")))}
        </div>
        <div class="gate {gate_class(auth.get("human_approval_required"), good_when_true=False)}">
          <strong>human_approval_required</strong>{html.escape(str(auth.get("human_approval_required")))}
        </div>
      </div>
      <p class="callout">法庭 verdict ≠ 执行授权。交互写回需 <code>make sop-console</code>；否则本页只读。</p>
    </header>

    <div class="tabs">
      <button type="button" class="tab-btn" data-panel="panel-owner-next">下一步</button>
      <button type="button" class="tab-btn" data-panel="panel-wizard">向导</button>
      <button type="button" class="tab-btn" data-panel="panel-court">法庭</button>
      <button type="button" class="tab-btn" data-panel="panel-chain">链路</button>
      <button type="button" class="tab-btn" data-panel="panel-debate">讨论</button>
      <button type="button" class="tab-btn" data-panel="panel-teams">专家队</button>
      <button type="button" class="tab-btn" data-panel="panel-more">更多</button>
    </div>

    {owner_html}
    {wizard_html}
    {court_html}

    <section id="panel-chain" class="tab-panel">
      <h2>可审计链路</h2>
      <p class="progress">{done} / {total} 步就绪 · {next_action}</p>
      <div class="steps">{"".join(steps_html)}</div>
    </section>

    <section id="panel-debate" class="tab-panel">
      <h2>讨论过程</h2>
      <p class="muted">真源：<code>03_debate_session.md</code></p>
      <h3 style="font-size:0.9rem;color:var(--muted)">冲突摘要</h3>
      {debate_conflicts or "<p class='muted'>—</p>"}
      <h3 style="font-size:0.9rem;color:var(--muted)">讨论纪要</h3>
      <ul>{minutes_html}</ul>
    </section>

    <section id="panel-teams" class="tab-panel">
      <h2>专家队评审</h2>
      <div class="teams">{"".join(teams_html) or "<p class='muted'>无 team_blocks</p>"}</div>
    </section>

    <section id="panel-more" class="tab-panel">
      <h2>关键前提（CAC）</h2>
      {cac_html or "<p class='muted'>—</p>"}
      <h2>分析产出</h2>
      {outputs_html or "<p class='muted'>无 outputs/*.md</p>"}
      <h2>下一步</h2>
      <div class="todo">{html.escape(data.get("todo") or "见 CASE_TODO.md")}</div>
    </section>

    <footer>
      Generated by scripts/render_case_dashboard.py · Phase 4 interactive SOP
    </footer>
  </div>
  <script type="application/json" id="case-data">{payload}</script>
  {wizard_js}
</body>
</html>
"""


def render_case(case_dir: Path, force: bool) -> Path:
    case_dir = case_dir.resolve()
    out = case_dir / "artifacts" / "CASE_DASHBOARD.html"
    if out.exists() and not force:
        raise FileExistsError(f"{out} exists; pass --force to overwrite")
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_case_data(case_dir)
    sync_case_todo(case_dir, data.get("lifecycle") or {})
    out.write_text(render_html(data), encoding="utf-8")
    return out


def render_index(roots: list[Path], force: bool) -> Path:
    index_path = ROOT / "cases" / "index.html"
    rows: list[dict[str, str]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for case_dir in sorted(root.iterdir()):
            if not case_dir.is_dir() or case_dir.name.startswith("."):
                continue
            intake = parse_frontmatter(case_dir / "01_case_intake.md")
            decision = parse_frontmatter(case_dir / "07_orchestrator_decision.md")
            lc = derive_owner_lifecycle(case_dir)
            dash = case_dir / "artifacts" / "CASE_DASHBOARD.html"
            link = rel_from_cases_index(case_dir) if dash.is_file() else ""
            rows.append(
                {
                    "bucket": root.name,
                    "case_id": str(intake.get("case_id", case_dir.name)),
                    "status": str(intake.get("status", "—")),
                    "topic": str(intake.get("topic", ""))[:80],
                    "link": link,
                    "lifecycle": lc.get("lifecycle", ""),
                    "lifecycle_label": LIFECYCLE_LABELS.get(lc.get("lifecycle", ""), ""),
                    "mtime": lc.get("mtime", ""),
                    "needs_execution": str(
                        decision.get("needs_execution", intake.get("needs_execution", "—"))
                    ),
                    "execution_authorized": str(
                        decision.get(
                            "execution_authorized", intake.get("execution_authorized", "—")
                        )
                    ),
                }
            )

    body_rows = []
    for row in rows:
        link_cell = (
            f'<a href="{html.escape(row["link"])}">Dashboard</a>'
            if row["link"]
            else '<span class="muted">未生成</span>'
        )
        body_rows.append(
            f"<tr><td>{html.escape(row['bucket'])}</td>"
            f"<td><code>{html.escape(row['case_id'])}</code></td>"
            f"<td><span class='lc'>{html.escape(row['lifecycle_label'])}</span></td>"
            f"<td>{html.escape(row['status'])}</td>"
            f"<td class='muted'>{html.escape(row['needs_execution'])} / {html.escape(row['execution_authorized'])}</td>"
            f"<td>{html.escape(row['mtime'])}</td>"
            f"<td>{html.escape(row['topic'])}</td><td>{link_cell}</td></tr>"
        )

    content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Harness Cases Index</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f1419; color: #e7ecf3; padding: 24px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #2d3a4f; padding: 10px; text-align: left; }}
    th {{ color: #8b9cb3; }}
    a {{ color: #3d8bfd; }}
    .muted {{ color: #8b9cb3; }}
    .lc {{ color: #3ecf8e; }}
    .start-box {{ background: #1a2332; border: 1px solid #2d3a4f; padding: 14px; border-radius: 8px; margin-bottom: 20px; }}
    code {{ font-size: 0.85rem; }}
  </style>
</head>
<body>
  <h1>Personal-Orchestrator Cases</h1>
  <div class="start-box">
    <strong>新建案件（同一 topic 请用新目录，不要覆盖旧案）</strong>
    <pre style="margin:8px 0 0;white-space:pre-wrap">make start TOPIC='你的 topic 原话' CASE_TYPE=career_direction RISK=high
python3 scripts/fork_case.py cases/active/CASE-旧案 --slug=fork-v2</pre>
  </div>
  <p class="muted">运行 <code>make dashboards</code> 刷新 · 交互 <code>make sop-console</code> · 文档 <code>docs/OWNER_JOURNEY.md</code></p>
  <table>
    <thead><tr><th>目录</th><th>case_id</th><th>阶段</th><th>status</th><th>执行授权</th><th>更新</th><th>topic</th><th>看板</th></tr></thead>
    <tbody>{"".join(body_rows)}</tbody>
  </table>
</body>
</html>
"""
    if index_path.exists() and not force:
        raise FileExistsError(f"{index_path} exists; pass --force")
    index_path.write_text(content, encoding="utf-8")
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render HTML case dashboard.")
    parser.add_argument("case_dirs", nargs="*", help="Case directory paths")
    parser.add_argument("--index", action="store_true", help="Write cases/index.html")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        if args.index:
            path = render_index([ROOT / "cases" / "active", ROOT / "cases" / "samples"], args.force)
            print(path)
        for raw in args.case_dirs:
            out = render_case(Path(raw), args.force)
            print(out)
        if not args.index and not args.case_dirs:
            parser.error("provide case_dirs and/or --index")
    except OSError as exc:
        print(f"ERROR: {exc}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
