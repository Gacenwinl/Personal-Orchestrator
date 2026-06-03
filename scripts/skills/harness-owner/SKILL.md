# harness-owner

**适用：** Owner 专用 profile、QQ Bot 私聊、或任何需要**不打开终端**操作 Harness 的场景。

## 前提

1. 本机已启动 Web Hub：`make hub`（`http://127.0.0.1:8765`）
2. 只操作 `Personal-Orchestrator-Harness` 的 `cases/` 目录
3. **禁止**未经 Owner 明确确认就调用 `confirm` 写 `execution_authorized: true`

## CLI（优先）

仓库内 CLI，无需记 HTTP：

```bash
python3 scripts/harness_hub_cli.py cases
python3 scripts/harness_hub_cli.py status cases/active/CASE-xxx
python3 scripts/harness_hub_cli.py doctor
python3 scripts/harness_hub_cli.py authorize-request cases/active/CASE-xxx --phase phase1
python3 scripts/harness_hub_cli.py confirm cases/active/CASE-xxx <token>
python3 scripts/harness_hub_cli.py court-dispatch cases/active/CASE-xxx
```

## QQ 口令映射（用户说 → 你执行）

| 用户说法 | 动作 |
|----------|------|
| `h cases` / 案件列表 | `harness_hub_cli.py cases` |
| `h status CASE-xxx` | `harness_hub_cli.py status …` |
| `h doctor` | `harness_hub_cli.py doctor` |
| `h authorize CASE-xxx` | `authorize-request`，把 **token** 和 `confirm <token>` 说明发给用户 |
| `confirm abcd1234`（用户回复） | `harness_hub_cli.py confirm CASE-xxx abcd1234` |
| `h court CASE-xxx` | 先 `doctor`；通过后再 `court-dispatch` |

## HTTP（备选）

```bash
curl -s http://127.0.0.1:8765/api/cases
curl -s "http://127.0.0.1:8765/api/case?path=cases/active/CASE-xxx"
curl -s http://127.0.0.1:8765/api/hermes/doctor
```

## 禁止

- 不要代替 Owner 确认授权（无 `confirm <token>` 不得 `execution_authorized: true`）
- 不要修改 `lessons/approved/`、`SOUL.md`、`HARNESS_ENGINE.md`
- 不要启动无人值守的求职投递或外网批量动作

## 安装

```bash
hermes skills install /path/to/Personal-Orchestrator-Harness/scripts/skills/harness-owner
```

详见 [integrations/qq_harness_bridge.md](../../../integrations/qq_harness_bridge.md)。
