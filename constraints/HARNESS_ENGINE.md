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
8. **禁止**在本 Harness 第一阶段自动调用外部 API 或无人值守跑 Hermes。

## 必须

1. 高风险动作 **必须** `human_approval_required: true` 且 Owner 明确同意。
2. `execution_authorized: true` **必须**与 `authorized_phase` 一致才允许 External Executor 开工。
3. Orchestrator **必须**独立验收（`11`），不得仅信 `10` 自报。
4. 案件 `completed` **必须**满足 `AGENTS.md` 可审计链路 12 环节（无执行案件可跳过 10–11，但须在 intake 注明并保留 9 的状态记录）。

## 角色

- 默认 Cursor = Orchestrator。
- Cursor 仅维护本仓库时为 Local Executor。
- Hermes / OpenClaw = External Executor。
