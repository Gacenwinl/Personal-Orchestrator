# Personal-Orchestrator-Harness

个人动态专家法庭 + Orchestrator/Executor 分层 Harness（第一阶段：Markdown）。

## 这是什么

不是 prompt 合集，而是一套**可审计案件生命周期**：立案 → 动态组队 → 辩论模式 → verdict → 关键前提检查 → Orchestrator 决策 →（可选）执行授权 → 任务书 → 验收 → lesson 沉淀。

## 角色（必读）

| 角色 | 谁 | 职责 |
|------|-----|------|
| Human Owner / Judge | 你 | 最终审批、高风险动作确认 |
| **Orchestrator** | **Cursor（默认）** | 全生命周期：立案、法庭、CAC、Phase、验收、lessons |
| Dynamic Expert Court | Orchestrator 调用的评审模块 | 输出 verdict，**无执行权** |
| **Local Executor** | Cursor **仅在本仓库**改文档/模板/脚本时 | 不对外网/账号/ Hermes 自动执行 |
| **External Executor** | Hermes / OpenClaw 等 | 经批准的任务书内原子执行 |

**Verdict ≠ 执行授权。** 见案件 frontmatter：`needs_execution`、`execution_authorized`、`authorized_phase`、`human_approval_required`。

## 30 分钟跑通

1. 读 [engine/ORCHESTRATOR_RUNBOOK.md](engine/ORCHESTRATOR_RUNBOOK.md)
2. 对照金样例 [cases/samples/CASE-001-mems-career-direction/](cases/samples/CASE-001-mems-career-direction/)
3. 用 `python3 scripts/new_case.py "你的 topic" --case-type career_direction --risk-tier high --needs-execution` 创建 `cases/active/CASE-xxx`
4. 可用 `python3 scripts/suggest_teams.py cases/active/CASE-xxx` 辅助生成 `02_team_selection.md`
5. 可用 `python3 scripts/suggest_modes.py cases/active/CASE-xxx` 辅助生成 `02b_mode_selection.md`
6. 团队定义见 [registry/teams/](registry/teams/)，输出结构见 [templates/04_team_verdict_block.md](templates/04_team_verdict_block.md)
7. 结案前运行 `python3 scripts/validate_case.py cases/active/CASE-xxx`，确保可审计链路与授权状态通过机械检查

## 目录

- `constraints/` — 硬约束（Harness Engine）
- `engine/` — Orchestrator 操作手册与生命周期
- `registry/` — 团队、模式、verdict、路由规则（真源）
- `templates/` — 案件产物骨架
- `prompts/` — 最小调用壳（指向 registry + templates）
- `cases/samples/` — 完整金样例
- `lessons/` — 经审计的教训
- `integrations/` — Hermes 等对接说明（第一阶段仅占位）

## 第一阶段明确不做

- 多模型 API 自动调用
- 修改 Hermes / OpenClaw 源码
- 自动执行外部任务（爬取、投递、删文件等）

## 与 OpenClaw_Workspace 的关系

本仓库**独立**。求职执行仍走 `~/OpenClaw_Workspace/hermes`；本 Harness 产出 `09_executor_instruction.md` 后由你审批，再**手工**交给 Hermes（见 [integrations/hermes_handoff.md](integrations/hermes_handoff.md)）。
