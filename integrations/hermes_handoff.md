# Hermes Handoff（Phase 1：手工，不改 Hermes 源码）

## 原则

- Harness 产出 `09_executor_instruction.md`。
- Owner 审批后，Orchestrator **复制**任务书到 Hermes 会话或 cron payload。
- Hermes 仍受 `~/OpenClaw_Workspace/hermes/data/` 内 HARD-RULES 约束；本 Harness 不替代其真源。

## 建议步骤

1. 在本仓库生成交接包：

```bash
python3 scripts/render_handoff.py cases/active/CASE-xxx
```

2. 确认 `execution_authorized: true` 且 `authorized_phase` 匹配。
3. 将 `09` 中 forbidden_actions 与 Hermes profile（如 jobintel）白名单对照。
4. 优先 `no_agent` + 脚本形态（若仅为 JD 收集），避免长 agent turn。
5. 执行后要求 Hermes 只填 Harness `10_execution_feedback.md` 对应字段到约定路径。

## 禁止（第一阶段）

- 自动创建 cron
- 修改 `hermes-agent` 仓库
- 将 `court_verdict_tier` 直接写入 Hermes prompt 作为执行令

## 参考

- OpenClaw jobchief 编排：`~/OpenClaw_Workspace/hermes/data/profiles/jobchief/AGENTS.md`
