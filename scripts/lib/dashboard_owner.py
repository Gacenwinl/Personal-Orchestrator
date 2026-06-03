"""Owner-next panel and automation status for CASE_DASHBOARD.html."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


LIFECYCLE_LABELS = {
    "draft": "立案中",
    "court_in_progress": "法庭进行中",
    "awaiting_owner_decision": "待决策",
    "analysis_complete": "分析结案",
    "awaiting_authorization": "待授权执行",
    "execution_active": "执行中",
    "completed": "已完成",
}


def load_automation_artifacts(case_dir: Path) -> dict[str, Any]:
    art = case_dir / "artifacts"
    out: dict[str, Any] = {}
    for name in ("court_dispatch.json", "daemon_state.json", "stage5_eval.json"):
        p = art / name
        if p.is_file():
            try:
                out[name] = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                out[name] = {"raw": p.read_text(encoding="utf-8")[:500]}
    log_path = art / "daemon.log"
    if log_path.is_file():
        lines = log_path.read_text(encoding="utf-8").splitlines()
        out["daemon_log_tail"] = "\n".join(lines[-8:])
    return out


def owner_next_panel_html(
    lifecycle: dict[str, Any], hermes: dict[str, Any], hub_mode: bool = False
) -> str:
    lc = lifecycle.get("lifecycle", "")
    label = LIFECYCLE_LABELS.get(lc, lc)
    headline = html.escape(str(lifecycle.get("headline", "")))
    case_rel = html.escape(str(lifecycle.get("case_dir", "")))

    actions_html = ""
    case_rel_raw = str(lifecycle.get("case_dir", ""))
    for index, action in enumerate(lifecycle.get("owner_actions") or [], 1):
        href = action.get("path") or ""
        if href and not href.startswith("http"):
            if hub_mode and case_rel_raw:
                from urllib.parse import quote

                link = (
                    f'<a href="/api/raw?path={quote(case_rel_raw)}&file={quote(href)}">'
                    f'{html.escape(action.get("title", ""))}</a>'
                )
            else:
                link = (
                    f'<a href="../{html.escape(href)}">'
                    f'{html.escape(action.get("title", ""))}</a>'
                )
        else:
            link = html.escape(action.get("title", ""))
        actions_html += f"<li>{index}. {link}</li>"

    outputs_html = ""
    for out in lifecycle.get("outputs") or []:
        href = out.get("href", "")
        if hub_mode and case_rel_raw and href.startswith("../"):
            from urllib.parse import quote

            rel_file = href.removeprefix("../")
            href = f"/api/raw?path={quote(case_rel_raw)}&file={quote(rel_file)}"
        outputs_html += (
            f'<li><a href="{html.escape(href)}">'
            f'{html.escape(out.get("title", out.get("name", "")))}</a></li>'
        )

    cmds_html = ""
    for cmd in lifecycle.get("suggested_commands") or []:
        cmds_html += (
            f'<div class="cmd-row">'
            f'<code>{html.escape(cmd)}</code> '
            f'<button type="button" class="btn secondary btn-copy-cmd" data-cmd="{html.escape(cmd)}">复制</button>'
            f"</div>"
        )

    hermes_level = hermes.get("level", "unknown")
    hermes_msg = html.escape(str(hermes.get("summary", "")))
    hermes_class = {"ok": "hermes-ok", "warn": "hermes-warn", "bad": "hermes-bad"}.get(
        hermes_level, ""
    )

    return f"""
    <section id="panel-owner-next" class="tab-panel">
      <h2>下一步（Owner）</h2>
      <p class="lifecycle-badge {html.escape(lc)}">{html.escape(label)}</p>
      <p class="callout">{headline}</p>
      <p class="muted">案件路径：<code>{case_rel}</code></p>

      <h3 class="subhead">你要做的事</h3>
      <ul class="owner-actions">{actions_html or "<li class='muted'>见 07_orchestrator_decision.md</li>"}</ul>

      <h3 class="subhead">分析产出</h3>
      <ul>{outputs_html or "<li class='muted'>无 outputs/*.md</li>"}</ul>

      <h3 class="subhead">常用命令</h3>
      <div class="cmd-list">{cmds_html}</div>

      <h3 class="subhead">Hermes 自动化</h3>
      <p class="hermes-status {hermes_class}" id="hermes-status-line">{hermes_msg}</p>
      {hub_automation_buttons(case_rel, hub_mode)}
    </section>
    """


def hub_automation_buttons(case_rel: str, hub_mode: bool) -> str:
    if not hub_mode:
        return (
            f'<p class="muted">自动法庭：<code>make hermes-doctor</code> 全绿后 '
            f'<code>make court-run CASE={case_rel}</code><br>'
            f'手册排班：<code>make court-launch CASE={case_rel}</code>（仅生成 md）</p>'
        )
    return f"""
      <div class="wizard-actions">
        <button type="button" class="btn secondary" id="btn-hermes-doctor">检测 Hermes</button>
        <button type="button" class="btn secondary" id="btn-court-launch">生成法庭手册</button>
        <button type="button" class="btn" id="btn-court-dispatch">派发 court-dispatch</button>
        <button type="button" class="btn secondary" id="btn-workflow-tick">workflow 单步</button>
      </div>
      <p class="muted">高级：<code>make court-run</code> 会启动长驻 kanban（终端）</p>
    """


def court_panel_enhanced_html(
    wizard: dict[str, Any],
    lifecycle: dict[str, Any],
    automation: dict[str, Any],
    hub_mode: bool = False,
) -> str:
    court_rows = ""
    for row in wizard.get("court_plan") or []:
        court_rows += (
            f"<tr><td>{html.escape(row.get('team_id',''))}</td>"
            f"<td><code>{html.escape(row.get('block_path',''))}</code></td>"
            f"<td>{html.escape(row.get('status',''))}</td></tr>"
        )
    if not court_rows:
        for team_id in wizard.get("court_teams") or []:
            court_rows += (
                f"<tr><td>{html.escape(team_id)}</td>"
                f"<td><code>artifacts/team_blocks/{html.escape(team_id)}.md</code></td>"
                f"<td>—</td></tr>"
            )

    auto_bits = ""
    if automation.get("court_dispatch.json"):
        auto_bits += "<p class='muted'>court_dispatch.json 已存在（已派发 swarm）</p>"
    if automation.get("daemon_state.json"):
        stage = automation["daemon_state.json"].get("stage", "?")
        auto_bits += f"<p class='muted'>workflow daemon 阶段：<code>{html.escape(str(stage))}</code></p>"
    if automation.get("daemon_log_tail"):
        auto_bits += (
            f"<pre class='api-log'>{html.escape(automation['daemon_log_tail'])}</pre>"
        )

    case_rel_raw = str(lifecycle.get("case_dir", ""))
    case_rel = html.escape(case_rel_raw)
    if hub_mode and case_rel_raw:
        from urllib.parse import quote

        plan_href = (
            f"/api/raw?path={quote(case_rel_raw)}&file={quote('artifacts/COURT_LAUNCH_PLAN.md')}"
        )
    else:
        plan_href = "../artifacts/COURT_LAUNCH_PLAN.md"
    court_btns = hub_automation_buttons(case_rel, hub_mode) if hub_mode else (
        f"<p><strong>生成手册</strong>：<code>make court-launch CASE={case_rel}</code></p>"
        f"<p><strong>自动并行</strong>：<code>make court-run CASE={case_rel}</code></p>"
    )
    return f"""
    <section id="panel-court" class="tab-panel">
      <h2>法庭</h2>
      {court_btns}
      {auto_bits}
      <table><thead><tr><th>team_id</th><th>block</th><th>status</th></tr></thead>
      <tbody>{court_rows or "<tr><td colspan='3' class='muted'>填写 02 后生成</td></tr>"}</tbody></table>
      <p><a href="{plan_href}">COURT_LAUNCH_PLAN.md</a></p>
    </section>
    """


def wizard_banner_if_complete(lifecycle: dict[str, Any]) -> str:
    if lifecycle.get("lifecycle") not in {"analysis_complete", "completed"}:
        return ""
    return (
        '<p class="banner-warn">审理链路已齐。请优先查看「<strong>下一步</strong>」Tab，'
        "无需再从向导补 00–07。</p>"
    )


OWNER_EXTRA_CSS = """
    .lifecycle-badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 0.8rem;
      border: 1px solid var(--border);
      margin-bottom: 12px;
    }
    .lifecycle-badge.analysis_complete, .lifecycle-badge.completed {
      border-color: var(--ok);
      color: var(--ok);
    }
    .lifecycle-badge.awaiting_authorization { border-color: var(--warn); color: var(--warn); }
    .subhead { font-size: 0.9rem; color: var(--muted); margin: 16px 0 8px; }
    .owner-actions li { margin-bottom: 8px; }
    .cmd-list { display: grid; gap: 8px; }
    .cmd-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .cmd-row code { font-size: 0.75rem; flex: 1; min-width: 200px; }
    .banner-warn {
      background: var(--bg);
      border-left: 3px solid var(--warn);
      padding: 10px 14px;
      margin-bottom: 12px;
      font-size: 0.9rem;
    }
    .hermes-status { padding: 10px; border-radius: 8px; background: var(--bg); }
    .hermes-ok { border-left: 3px solid var(--ok); }
    .hermes-warn { border-left: 3px solid var(--warn); }
    .hermes-bad { border-left: 3px solid var(--bad); }
"""
