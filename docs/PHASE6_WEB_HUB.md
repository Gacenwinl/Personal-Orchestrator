# Phase 6：Web Hub（零终端日常）

在 Phase 4 `case_sop_server` 之上，提供**单页 Hub** 托管案件列表、立案、看板与法庭 API。

## 一键启动

```bash
make hub
```

浏览器打开 `http://127.0.0.1:8765/`。

`sop-console` 与 `hub` 为同一服务；`hub` 会后台启动并 `open` 浏览器。

## 能做什么（无需终端）

| 操作 | Hub |
|------|-----|
| 新建案件 | 首页表单 → `POST /api/start` |
| Fork | 首页 Fork 表单 |
| 案件列表 | 首页表格 / `GET /api/cases` |
| 看板 | `/case?path=cases/active/CASE-xxx` |
| PATCH / 授权 | 看板「向导」Tab |
| Hermes doctor | 按钮 / `GET /api/hermes/doctor` |
| 法庭手册 | `POST /api/court-launch` |
| court-dispatch | `POST /api/court-dispatch`（后台 job） |
| workflow 单步 | `POST /api/workflow/tick` |

## 仍建议终端/Cursor 的场景

- 填写 `artifacts/team_blocks/*.md`、长文 05/07
- `make court-run` 长驻 kanban daemon
- 首次 `make hermes-setup`

## API 摘要

- `GET /` — Hub
- `GET /case?path=…` — 交互看板（同源 API）
- `GET /api/raw?path=…&file=…` — 读案件内 md/json
- `GET /api/jobs/{id}` — 异步任务状态

授权与 [HARNESS_ENGINE.md](../constraints/HARNESS_ENGINE.md) 一致：`owner_confirmed` 或 QQ `confirm <token>`。

## QQ Bot

见 [integrations/qq_harness_bridge.md](../integrations/qq_harness_bridge.md) 与 skill `scripts/skills/harness-owner`。

## 验收

```bash
make smoke
python3 scripts/case_sop_server.py --check
```

## 回滚

停用 Hub，继续 `make dashboard` + 手工编辑 Markdown 即可。
