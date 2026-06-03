# Harness Engine — 硬约束（真源）

违反任一条 → 任务必须 `stopped` 并回报 Human Owner。

## 禁止（Executor 与 Orchestrator 均适用）

1. **禁止**自动提交岗位申请、发送邮件、公开发布。
2. **禁止**删除未备份文件；优先可恢复操作。
3. **禁止**修改系统关键配置（crontab、nginx、他人仓库）未经 Owner 确认。
4. **禁止**越权访问账号、绕过验证码/风控/反爬。
5. **禁止** Executor 自行扩大任务范围（未写入 `09` 的步骤一律不做）。
6. **禁止**将 Court `verdict` 直接当作执行授权。
7. **禁止** Executor 写入 `lessons/approved/`、`SOUL.md` 或篡改 `HARNESS_ENGINE.md`。
8. **Phase 5 自动化授权条款**（取代原 Phase 1 禁止条款）：
   - Phase A（审理）法庭辩论 **可以**通过 `hermes kanban swarm` 自动并行执行，前提是已在案件目录下写入 `artifacts/court_dispatch.json`（由 `court_dispatch.py` 创建）。
   - **Phase A→B 授权门仍为硬门控**：`workflow_daemon.py` 不得自动写 `execution_authorized: true`，必须等待 Owner 通过 SOP Console 或手动修改。
   - Phase B 工单发送（`hermes send`）仅在 `execution_authorized: true` 且 `human_approval_required: false` 时允许。
   - **禁止** court skill / synthesizer 写 `execution_authorized`、`needs_execution` 或任何授权字段。
   - **禁止**自动创建 Hermes cron 或无人值守的求职/投递动作。
   - Executor 自报（`10`）仍不升格为 lesson；仍须 Orchestrator 独立验收（`11`）。

## 必须

1. 高风险动作 **必须** `human_approval_required: true` 且 Owner 明确同意。
2. `execution_authorized: true` **必须**与 `authorized_phase` 一致才允许 External Executor 开工。
3. Orchestrator **必须**独立验收（`11`），不得仅信 `10` 自报。
4. 案件 `completed` **必须**满足 `AGENTS.md` 可审计链路 12 环节（无执行案件可跳过 10–11，但须在 intake 注明并保留 9 的状态记录）。

## 角色

- 默认 Cursor = Orchestrator。
- Cursor 仅维护本仓库时为 Local Executor。
- Hermes / OpenClaw = External Executor。
