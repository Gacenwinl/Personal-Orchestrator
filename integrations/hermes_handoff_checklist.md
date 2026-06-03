# Hermes Handoff Checklist

配合 [hermes_handoff.md](hermes_handoff.md) 使用。全部为**手工**步骤；禁止在本 Harness 第一阶段自动创建 cron 或改 Hermes 源码。

## A. 授权前（审理 Session 结束）

- [ ] `python3 scripts/validate_case.py cases/active/CASE-xxx` → **PASS**（无 ERROR）
- [ ] `01` 与 `07` 中 `execution_authorized: true` **仅当** Owner 已明确批准
- [ ] `human_approval_required: false` 时方可授权（与 `execution_authorized: true` 不得同时为 true，见校验脚本）
- [ ] `authorized_phase` 与计划 Phase 一致（如 `phase2`）
- [ ] `06_critical_assumption_check.md` 已填且针对**本案**前提（非复制旧案）
- [ ] 未误用 `court_verdict_tier` 作为执行依据

## B. 编写 09 任务书

- [ ] 使用 [templates/09_executor_instruction.md](../templates/09_executor_instruction.md)
- [ ] frontmatter：`execution_authorized: true`，`phase` 与 `authorized_phase` 一致
- [ ] 正文必含三节：**禁止事项**、**验收标准**、**停止并回报条件**
- [ ] `forbidden_actions` 与 Hermes profile 白名单对照（如 `~/OpenClaw_Workspace/hermes/data/profiles/jobintel/` 或 jobchief 相关 HARD-RULES）
- [ ] 范围限定为原子步骤；无「顺便」扩大 scope

## C. 生成交接包

```bash
python3 scripts/render_handoff.py cases/active/CASE-xxx
```

- [ ] 仅当 B 节全部满足后运行
- [ ] 检查 `artifacts/HANDOFF_hermes_*.md` 中 phase 与 forbidden 摘要
- [ ] **手工**复制到 Hermes 会话；不自动粘贴、不自动 cron

## D. OpenClaw / Cursor 会话协议

1. **新 Session** 执行 Phase B（只读 `08`/`09` + 输入），不与审理 Session 混上下文。
2. 粘贴顺序建议：`09` 全文 → HANDOFF 摘要 → 输入文件路径列表。
3. 要求 Executor **只**更新本案 `10_execution_feedback.md`（事实与路径），不写 `lessons/approved/`。
4. Cursor 若做本地简历草稿，仍须 `execution_authorized: true` 且写在 `09` 范围内。

## E. 执行后（Orchestrator 验收）

- [ ] 收集 `10_execution_feedback.md`
- [ ] **独立**填写 `11_acceptance_review.md`（不信 10 自报）
- [ ] 对照 `09` 验收标准与 B 系列 / 09 内前提逐项勾选
- [ ] 通过后再考虑 `12_lesson_proposal.md` 升格

## F. 禁止（第一阶段）

- 自动 `render_handoff` 后触发 Hermes cron
- 修改 `hermes-agent` 或 OpenClaw 仓库
- 将法庭 tier 写入 Hermes system prompt 作为执行令
- 在未授权时生成 HANDOFF 并对外执行

## 相关命令

```bash
python3 scripts/case_status.py cases/active/CASE-xxx
python3 scripts/validate_case.py cases/active/CASE-xxx
```
