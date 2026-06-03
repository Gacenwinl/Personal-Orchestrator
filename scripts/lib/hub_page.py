"""Web Hub landing page HTML."""

from __future__ import annotations

import html
import json
from typing import Any


def render_hub_page(cases: list[dict[str, Any]] | None = None) -> str:
    rows = ""
    for row in cases or []:
        url = html.escape(row.get("dashboard_url", ""))
        rows += (
            f"<tr>"
            f"<td>{html.escape(row.get('bucket', ''))}</td>"
            f"<td><a href=\"{url}\"><code>{html.escape(row.get('case_id', ''))}</code></a></td>"
            f"<td><span class='lc'>{html.escape(row.get('lifecycle_label', ''))}</span></td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td class='muted'>{html.escape(str(row.get('needs_execution')))} / "
            f"{html.escape(str(row.get('execution_authorized')))}</td>"
            f"<td>{html.escape(row.get('mtime', ''))}</td>"
            f"<td>{html.escape(row.get('topic', ''))}</td>"
            f"</tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Harness Web Hub</title>
  <style>
    :root {{
      --bg: #0f1419; --surface: #1a2332; --border: #2d3a4f;
      --text: #e7ecf3; --muted: #8b9cb3; --accent: #3d8bfd; --ok: #3ecf8e;
    }}
    body {{ margin: 0; font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 24px; }}
    h1 {{ margin-top: 0; }}
    .grid {{ display: grid; gap: 20px; grid-template-columns: 1fr 1fr; }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 18px; }}
    label {{ display: block; font-size: 0.85rem; color: var(--muted); margin: 8px 0 4px; }}
    input, select, textarea {{
      width: 100%; padding: 8px; border-radius: 8px; border: 1px solid var(--border);
      background: var(--bg); color: var(--text); box-sizing: border-box;
    }}
    textarea {{ min-height: 80px; }}
    .btn {{
      margin-top: 12px; padding: 10px 16px; border: none; border-radius: 8px;
      background: var(--accent); color: #fff; cursor: pointer;
    }}
    .btn.secondary {{ background: var(--border); color: var(--text); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 12px; }}
    th, td {{ border: 1px solid var(--border); padding: 8px; text-align: left; }}
    th {{ color: var(--muted); }}
    a {{ color: var(--accent); }}
    .lc {{ color: var(--ok); }}
    .muted {{ color: var(--muted); font-size: 0.85rem; }}
    #log {{ white-space: pre-wrap; font-size: 0.8rem; color: var(--muted); margin-top: 12px; }}
    .hermes-box {{ margin-top: 10px; padding: 10px; border-radius: 8px; background: var(--bg); }}
  </style>
</head>
<body>
  <h1>Harness Web Hub</h1>
  <p class="muted">本机 <code>http://127.0.0.1:8765</code> · 日常零终端 · 文档 <code>docs/OWNER_JOURNEY.md</code></p>

  <div class="grid">
    <div class="card">
      <h2>新建案件</h2>
      <form id="form-start">
        <label>Topic（原话）</label>
        <textarea name="topic" required placeholder="你的问题或目标…"></textarea>
        <label>case_type</label>
        <select name="case_type">
          <option value="career_direction">career_direction</option>
          <option value="technical_route">technical_route</option>
        </select>
        <label>risk_tier</label>
        <select name="risk_tier">
          <option value="high" selected>high</option>
          <option value="medium">medium</option>
          <option value="low">low</option>
        </select>
        <label><input type="checkbox" name="needs_execution" /> needs_execution</label>
        <button type="submit" class="btn">创建并打开看板</button>
      </form>
    </div>
    <div class="card">
      <h2>Fork（同一 topic 新目录）</h2>
      <form id="form-fork">
        <label>源案件路径</label>
        <input name="from" placeholder="cases/active/CASE-xxx" required />
        <label>slug</label>
        <input name="slug" placeholder="fork-v2" />
        <button type="submit" class="btn secondary">Fork</button>
      </form>
      <h2 style="margin-top:20px">Hermes</h2>
      <button type="button" class="btn secondary" id="btn-doctor">检测 Hermes 就绪</button>
      <div id="hermes-result" class="hermes-box muted">—</div>
    </div>
  </div>

  <div class="card" style="margin-top:20px">
    <h2>案件列表</h2>
    <button type="button" class="btn secondary" id="btn-refresh">刷新列表</button>
    <table>
      <thead><tr><th>目录</th><th>case_id</th><th>阶段</th><th>status</th><th>授权</th><th>更新</th><th>topic</th></tr></thead>
      <tbody id="case-rows">{rows}</tbody>
    </table>
  </div>
  <pre id="log"></pre>

  <script>
  const logEl = document.getElementById("log");
  function log(msg) {{ logEl.textContent = (logEl.textContent + "\\n" + msg).trim(); }}

  async function api(path, opts) {{
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({{}}));
    if (!res.ok) throw new Error(data.error || res.statusText);
    return data;
  }}

  function renderCases(cases) {{
    const tbody = document.getElementById("case-rows");
    tbody.innerHTML = cases.map((row) => `
      <tr>
        <td>${{row.bucket}}</td>
        <td><a href="${{row.dashboard_url}}"><code>${{row.case_id}}</code></a></td>
        <td><span class="lc">${{row.lifecycle_label || row.lifecycle}}</span></td>
        <td>${{row.status}}</td>
        <td class="muted">${{row.needs_execution}} / ${{row.execution_authorized}}</td>
        <td>${{row.mtime}}</td>
        <td>${{row.topic}}</td>
      </tr>`).join("");
  }}

  document.getElementById("btn-refresh").addEventListener("click", async () => {{
    try {{
      const data = await api("/api/cases");
      renderCases(data.cases || []);
      log("列表已刷新");
    }} catch (e) {{ log(e.message); }}
  }});

  document.getElementById("form-start").addEventListener("submit", async (ev) => {{
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {{
      const data = await api("/api/start", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          topic: fd.get("topic"),
          case_type: fd.get("case_type"),
          risk_tier: fd.get("risk_tier"),
          needs_execution: fd.get("needs_execution") === "on",
        }}),
      }});
      log("已创建: " + data.case_dir);
      location.href = data.dashboard_url;
    }} catch (e) {{ log(e.message); }}
  }});

  document.getElementById("form-fork").addEventListener("submit", async (ev) => {{
    ev.preventDefault();
    const fd = new FormData(ev.target);
    try {{
      const data = await api("/api/fork", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          from: fd.get("from"),
          slug: fd.get("slug") || null,
        }}),
      }});
      log("已 fork: " + data.case_dir);
      location.href = data.dashboard_url;
    }} catch (e) {{ log(e.message); }}
  }});

  document.getElementById("btn-doctor").addEventListener("click", async () => {{
    const box = document.getElementById("hermes-result");
    try {{
      const data = await api("/api/hermes/doctor");
      box.textContent = data.summary + "\\n" + (data.checks || []).map((c) => c.id + ": " + c.status).join("\\n");
      log("doctor: " + data.level);
    }} catch (e) {{ box.textContent = e.message; }}
  }});
  </script>
</body>
</html>
"""
