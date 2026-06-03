# 工作流测试：小米 MiMo（与 OpenClaw 一致）

## 当前默认

| 项 | 值 |
|----|-----|
| Provider | `xiaomi` |
| Model | `mimo-v2.5-pro` |
| 完整 ID | `xiaomi/mimo-v2.5-pro` |
| API Base | `https://token-plan-cn.xiaomimimo.com/v1` |
| 配置档 | `registry/model_defaults.yaml` → `workflow_test` |

与 Hermes 一致：`~/OpenClaw_Workspace/hermes/data/config.yaml` 中 `model: xiaomi/mimo-v2.5-pro`。

## API Key

不要写入本仓库。沿用 OpenClaw 环境即可：

- 主环境变量：`XIAOMI_API_KEY` 或 `XIAOMI_TOKEN_PLAN_CN_API_KEY`
- 常见位置：`~/.openclaw/.env`
- 说明见：`~/OpenClaw_Workspace/hermes/data/.env.example`

## 在 Cursor 里怎么测工作流

1. **Orchestrator 会话**（Cursor）：选用 `xiaomi/mimo-v2.5-pro`（若 Cursor 已配置该 OpenAI-compatible 端点）。
2. 创建案件：

```bash
python3 scripts/new_case.py "测试 topic" --case-type career_direction --risk-tier high --needs-execution --prepare
```

3. 按 `engine/ORCHESTRATOR_RUNBOOK.md` 填写 `03`–`07`；各 team 读 `registry/teams/<id>.yaml` + 填 `artifacts/team_blocks/`。
4. `02b_mode_selection.md` 中模型表应已默认 MiMo（`suggest_modes.py --write` 会从 `model_defaults` 填充）。
5. 结案：`python3 scripts/validate_case.py cases/active/CASE-xxx`

## 测试期与正式期区别

| | 工作流测试（现在） | 正式审理（以后） |
|--|-------------------|------------------|
| 模型 | 单厂商 MiMo | 多厂商减偏差 |
| 目标 | 跑通 12 步链路 | 降低同源盲区 |
| 规则 | `model_routing_rules.yaml` → `workflow_test_assignments` | `production_assignments` |

## 切换正式多厂商时

1. 改 `registry/model_defaults.yaml` 的 `active_profile: production`
2. 按 `production_assignments` 手填 `02b` 模型表
3. 在 `memory/model_bias_notes.md` 记录各厂商表现
