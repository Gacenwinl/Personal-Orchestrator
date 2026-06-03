# QQ Bot ↔ Harness Web Hub 桥接

## 架构

- **Web Hub**（真源 API）：`make hub` → `http://127.0.0.1:8765`
- **Hermes qqbot**：OpenClaw gateway 已有 `qqbot` 通道
- **harness-owner skill**：把 QQ 短指令转成 `harness_hub_cli.py` 或 Hub HTTP

## 前置条件

1. Mac 上 Harness 仓库路径已知（如 `~/Personal-Orchestrator-Harness`）
2. `make hub` 已运行（或 LaunchAgent 常驻 `case_sop_server.py`）
3. Hermes profile 已安装 skill：

```bash
hermes skills install ~/Personal-Orchestrator-Harness/scripts/skills/harness-owner
```

4. QQ 消息路由到带该 skill 的 profile（如 `jobchief` 或专用 `harness-owner` profile）
5. OpenClaw `allowed_channels` 仅包含你的 QQ open_id（勿 widen 到公网群）

## 命令表

| QQ 口令 | CLI |
|---------|-----|
| `h cases` | `python3 scripts/harness_hub_cli.py cases` |
| `h status <case_id>` | `… status cases/active/<case_id>` |
| `h doctor` | `… doctor` |
| `h authorize <case>` | `… authorize-request …` → 回复 token |
| `confirm <token>` | `… confirm <case> <token>` |
| `h court <case>` | `… court-dispatch …`（doctor 须非 bad） |

## 授权安全流

1. 用户：`h authorize CASE-xxx`
2. Bot 返回：`确认码 abcd1234`，请回复 `confirm abcd1234`
3. 用户明确回复后，Bot 调用 `/api/qq/confirm`
4. Hub 写入 `01`/`07` 四字段（与看板授权闸门一致）

**禁止**跳过 confirm 直接授权。

## 故障

| 现象 | 处理 |
|------|------|
| Hub 未运行 | `make hub` |
| doctor bad | `make hermes-setup` |
| 找不到案件 | 用 `h cases` 看完整 `case_dir` |

## 不做

- 不把 8765 暴露到公网
- 不改 Hermes-Agent 源码
- QQ 内不写 04/05/07 长文（仍用 Cursor Orchestrator）
