# CASE-001 金样例说明

**状态：** `completed`（演示全链路，Phase1 产出为 mock）

## 可审计链路核对

| # | 环节 | 文件 |
|---|------|------|
| 1 | 原始意图 | 00_owner_intent.md |
| 2 | 案件定义 | 01_case_intake.md |
| 3 | 团队选择理由 | 02_team_selection.md |
| 4 | 模式选择理由 | 02b_mode_selection.md |
| 5 | 团队评审块 | artifacts/team_blocks/*.md |
| 6 | 汇总 verdict | 05_court_summary.md |
| 7 | 关键前提检查 | 06_critical_assumption_check.md |
| 8 | Orchestrator 决策 | 07_orchestrator_decision.md |
| 9 | 执行授权状态 | 01 + 07 frontmatter |
| 10 | 执行任务书 | 09_executor_instruction.md |
| 11 | 验收结果 | 11_acceptance_review.md |
| 12 | lesson proposal | 12_lesson_proposal.md |

## 教学点

- `court_verdict_tier: RECOMMENDED_WITH_MODIFICATIONS` 与 `execution_authorized: true` **可同时存在**，但后者仅因 Owner 批准 **phase1**，不代表「主攻」已授权。
- `critical_assumption` 在第一版即为核心团队（见 02、06）。

## 复现

1. 复制 `templates/` 到 `cases/active/CASE-YYYYMMDD-xxx/`。
2. 按 [engine/ORCHESTRATOR_RUNBOOK.md](../../../engine/ORCHESTRATOR_RUNBOOK.md) 纯文本步骤执行。
