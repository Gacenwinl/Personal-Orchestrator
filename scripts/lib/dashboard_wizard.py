"""Interactive SOP wizard panel for CASE_DASHBOARD.html."""

from __future__ import annotations

import html
import json
from typing import Any

SOP_API = "http://127.0.0.1:8765"


def wizard_panel_html(wizard: dict[str, Any], banner: str = "") -> str:
    step = wizard.get("current_step") or {}
    auth = wizard.get("auth") or {}
    prompt = html.escape(str(wizard.get("cursor_prompt", "")))
    next_action = html.escape(str(wizard.get("next_action", "")))
    cli = html.escape(str((wizard.get("cli_hint") or "")))
    case_rel = html.escape(str(wizard.get("case_dir", "")))
    step_file = html.escape(str(step.get("file") or ""))
    step_label = html.escape(str(step.get("label") or ""))
    step_key = html.escape(str(step.get("key") or ""))

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

    return f"""
    <section id="panel-wizard" class="tab-panel">
      <h2>交互向导</h2>
      {banner}
      <p class="muted" id="sop-status">检测本机 SOP Console…</p>
      <div class="wizard-current">
        <span class="badge">当前步：{step_label}</span>
        <code>{step_key}</code> → <a href="../{step_file}" id="wizard-file-link">{step_file}</a>
      </div>
      <p class="callout">{next_action}</p>
      <p class="muted cli-hint">{cli}</p>
      <div class="wizard-actions">
        <button type="button" class="btn" id="btn-copy-prompt">复制 Cursor 口令</button>
        <button type="button" class="btn secondary" id="btn-regenerate">刷新看板</button>
      </div>
      <textarea id="cursor-prompt" readonly rows="6">{prompt}</textarea>

      <h3 style="font-size:0.9rem;margin-top:20px">快速写回（需 SOP Console）</h3>
      <form id="patch-form" class="patch-form">
        <label>目标 <select name="patch_target"><option value="intake">01 intake</option><option value="decision">07 decision</option></select></label>
        <label>status <input name="status" placeholder="draft / in_progress …" /></label>
        <label>needs_execution <select name="needs_execution"><option value="">—</option><option>true</option><option>false</option></select></label>
        <label>execution_authorized <select name="execution_authorized"><option value="">—</option><option>true</option><option>false</option></select></label>
        <label>authorized_phase <input name="authorized_phase" placeholder="phase1" /></label>
        <label>human_approval_required <select name="human_approval_required"><option value="">—</option><option>true</option><option>false</option></select></label>
        <label>讨论纪要 <input name="debate_minute" placeholder="追加到 03" /></label>
        <label class="check"><input type="checkbox" name="owner_confirmed" /> Owner 已确认（授权字段必填）</label>
        <button type="submit" class="btn">PATCH 写回</button>
      </form>
      <form id="authorize-form" class="patch-form">
        <h3 style="font-size:0.9rem">授权闸门</h3>
        <p class="muted">仅当 Owner 已口头/书面批准时勾选并提交。</p>
        <label class="check"><input type="checkbox" name="owner_confirmed" required /> Owner 确认授权</label>
        <label>authorized_phase <input name="authorized_phase" value="{html.escape(str(auth.get('authorized_phase') or ''))}" /></label>
        <button type="submit" class="btn warn">authorize（写 01+07）</button>
      </form>
      <pre id="api-log" class="api-log"></pre>
    </section>
"""


def wizard_script(case_rel: str, wizard: dict[str, Any], lifecycle: dict[str, Any]) -> str:
    payload = json.dumps(
        {"case_dir": case_rel, "wizard": wizard, "lifecycle": lifecycle},
        ensure_ascii=False,
    )
    default_tab = lifecycle.get("default_tab", "wizard")
    return f"""
<script>
(function() {{
  const SOP_API = {json.dumps(SOP_API)};
  const BOOT = {payload};
  const logEl = document.getElementById("api-log");
  const statusEl = document.getElementById("sop-status");
  const promptEl = document.getElementById("cursor-prompt");

  function log(msg) {{
    if (logEl) logEl.textContent = (logEl.textContent + "\\n" + msg).trim();
  }}

  async function api(path, opts) {{
    const res = await fetch(SOP_API + path, opts);
    const data = await res.json().catch(() => ({{}}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }}

  async function refreshWizard() {{
    try {{
      const state = await api("/api/case?path=" + encodeURIComponent(BOOT.case_dir));
      statusEl.textContent = "SOP Console 已连接";
      statusEl.className = "muted ok";
      if (state.cursor_prompt) promptEl.value = state.cursor_prompt;
      const step = state.current_step || {{}};
      const link = document.getElementById("wizard-file-link");
      if (link && step.file) {{
        link.href = "../" + step.file;
        link.textContent = step.file;
      }}
    }} catch (e) {{
      statusEl.textContent = "只读模式（未启动 make sop-console）";
      statusEl.className = "muted";
    }}
  }}

  function activateTab(panelId) {{
    document.querySelectorAll(".tab-btn").forEach((b) => {{
      b.classList.toggle("active", b.dataset.panel === panelId);
    }});
    document.querySelectorAll(".tab-panel").forEach((p) => {{
      p.classList.toggle("active", p.id === panelId);
    }});
  }}
  document.querySelectorAll(".tab-btn").forEach((btn) => {{
    btn.addEventListener("click", () => activateTab(btn.dataset.panel));
  }});
  document.querySelectorAll(".btn-copy-cmd").forEach((btn) => {{
    btn.addEventListener("click", () => {{
      navigator.clipboard.writeText(btn.dataset.cmd || "").then(() => log("已复制命令"));
    }});
  }});
  activateTab(BOOT.lifecycle.default_tab || "{default_tab}");

  document.getElementById("btn-copy-prompt").addEventListener("click", () => {{
    navigator.clipboard.writeText(promptEl.value).then(() => log("已复制口令"));
  }});

  document.getElementById("btn-regenerate").addEventListener("click", async () => {{
    try {{
      await api("/api/regenerate", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{ path: BOOT.case_dir }}),
      }});
      log("看板已重生；请刷新浏览器");
      location.reload();
    }} catch (e) {{ log("regenerate: " + e.message); }}
  }});

  function fieldsFromForm(form) {{
    const fields = {{}};
    ["status","authorized_phase"].forEach((k) => {{
      const v = form.elements[k]?.value?.trim();
      if (v) fields[k] = v;
    }});
    ["needs_execution","execution_authorized","human_approval_required"].forEach((k) => {{
      const v = form.elements[k]?.value;
      if (v === "true") fields[k] = true;
      if (v === "false") fields[k] = false;
    }});
    return fields;
  }}

  document.getElementById("patch-form").addEventListener("submit", async (ev) => {{
    ev.preventDefault();
    const form = ev.target;
    try {{
      const body = {{
        path: BOOT.case_dir,
        target: form.patch_target.value,
        fields: fieldsFromForm(form),
        owner_confirmed: form.owner_confirmed.checked,
      }};
      const minute = form.debate_minute.value.trim();
      if (minute) body.debate_minute = minute;
      await api("/api/patch", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify(body),
      }});
      log("PATCH OK");
      refreshWizard();
    }} catch (e) {{ log("PATCH: " + e.message); }}
  }});

  document.getElementById("authorize-form").addEventListener("submit", async (ev) => {{
    ev.preventDefault();
    const form = ev.target;
    if (!form.owner_confirmed.checked) {{
      log("authorize: 需要 Owner 确认");
      return;
    }}
    try {{
      await api("/api/authorize", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          path: BOOT.case_dir,
          owner_confirmed: true,
          fields: {{
            needs_execution: true,
            execution_authorized: true,
            authorized_phase: form.authorized_phase.value.trim() || "phase1",
            human_approval_required: false,
          }},
        }}),
      }});
      log("authorize OK");
      refreshWizard();
    }} catch (e) {{ log("authorize: " + e.message); }}
  }});

  refreshWizard();
}})();
</script>
"""


WIZARD_EXTRA_CSS = """
    .tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .tab-btn {
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
      cursor: pointer;
      font-size: 0.85rem;
    }
    .tab-btn.active { border-color: var(--accent); color: var(--accent); }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .btn {
      padding: 8px 14px;
      border-radius: 8px;
      border: none;
      background: var(--accent);
      color: #fff;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .btn.secondary { background: var(--border); color: var(--text); }
    .btn.warn { background: var(--warn); color: #111; }
    .wizard-actions { display: flex; gap: 10px; margin: 12px 0; flex-wrap: wrap; }
    #cursor-prompt {
      width: 100%;
      font-family: ui-monospace, monospace;
      font-size: 0.8rem;
      background: var(--bg);
      color: var(--text);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
    }
    .patch-form {
      display: grid;
      gap: 10px;
      max-width: 520px;
      font-size: 0.85rem;
    }
    .patch-form label { display: flex; flex-direction: column; gap: 4px; color: var(--muted); }
    .patch-form label.check { flex-direction: row; align-items: center; gap: 8px; color: var(--text); }
    .patch-form input, .patch-form select {
      padding: 8px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text);
    }
    .api-log {
      margin-top: 12px;
      padding: 10px;
      background: var(--bg);
      border-radius: 8px;
      font-size: 0.75rem;
      color: var(--muted);
      min-height: 2em;
      white-space: pre-wrap;
    }
    .muted.ok { color: var(--ok); }
    .wizard-current { margin-bottom: 12px; }
"""
