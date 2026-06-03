# Phase 4：交互推动 SOP

在 Phase 3 只读 HTML 看板之上，增加本机 **SOP Console**（写回 + 刷新）与看板内 **向导 / 法庭** 标签页。不自动调用 Hermes、cron 或多模型 API。

## 三层能力

| 层 | 能力 | 不做 |
|----|------|------|
| **4a 导航** | 当前步、next_action、复制 Cursor 口令、打开 md | 自动 Hermes |
| **4b 写回** | `127.0.0.1` PATCH 白名单 frontmatter、`validate_case` 一致授权闸门 | 无 Owner 确认设 `execution_authorized: true` |
| **4c 法庭启动器** | `COURT_LAUNCH_PLAN.md` + 看板法庭 Tab | 并行调外部 API |

## 快速开始

```bash
# 推荐：Web Hub（立案 + 看板 + API 一体）
make hub
# → http://127.0.0.1:8765/ → 点案件 →「向导」Tab

# 离线备份：file:// 看板仍需 make sop-console 写回
make dashboard CASE=cases/active/CASE-xxx
make sop-console
open cases/index.html
```

未启动 server 时看板仍可 **只读** 浏览；写回按钮会提示只读模式。

## Makefile

| 目标 | 说明 |
|------|------|
| `make sop-console` | `python3 scripts/case_sop_server.py` @ `127.0.0.1:8765` |
| `make dashboard CASE=…` | 生成/覆盖 `artifacts/CASE_DASHBOARD.html` |
| `make court-launch CASE=…` | 生成 `artifacts/COURT_LAUNCH_PLAN.md` |

## API（本机）

- `GET /api/case?path=cases/active/CASE-xxx` — wizard JSON
- `POST /api/patch` — `{ path, target: intake|decision, fields, debate_minute?, owner_confirmed }`
- `POST /api/authorize` — 二次确认 + 同步写 `01`/`07` 四字段
- `POST /api/regenerate` — 重跑 `render_case_dashboard.py --force`

授权失败返回 **403**（与 `validate_case.py` 一致）。

## 真源与共享库

- 链路逻辑：`scripts/lib/case_chain.py`（`case_status`、看板、server 共用）
- 步进口令：`registry/sop_wizard_steps.yaml`

## 验收

```bash
make smoke
python3 scripts/validate_case.py cases/active/CASE-20260603-msc-us-phd-agent-pi-outreach
python3 scripts/case_sop_server.py --check
```

手动：`make sop-console` → 看板向导 → PATCH status → 刷新看板。

## 回滚

停用 `make sop-console`，继续 `make dashboard` 纯 Markdown 工作流即可。
