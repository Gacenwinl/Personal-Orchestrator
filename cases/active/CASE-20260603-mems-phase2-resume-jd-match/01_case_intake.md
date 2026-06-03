---
case_id: CASE-20260603-mems-phase2-resume-jd-match
status: instruction_issued
case_type: career_direction
risk_tier: high
topic: "在 CASE-001 Phase1 结论与 JD 池证据基础上，评估是否进入 Phase2（方向决策 / 简历与 JD 匹配深化）"
owner_intent_ref: 00_owner_intent.md
predecessor_case: CASE-001-mems-career-direction

needs_execution: true
execution_authorized: true
authorized_phase: phase2
human_approval_required: false

court_verdict_tier: RECOMMENDED_WITH_MODIFICATIONS
cac_required: true
cac_exempt_reason: null
---

# Case Intake

## 案件摘要

Phase2 已授权：在 Phase1 池证据基础上完成 fit 矩阵、5 条 JD excerpt、简历 v2 草稿与方向备忘；**不投递、不登录**。

## 成功标准

- 见 `09_executor_instruction.md` 验收标准；Orchestrator 独立填 `11`。

## 约束与时间预算

- 执行预算：约 1 个工作日（Hermes/手工等效）。
- 证据仍为金样例池时，11 验收须注明 mock 限制。

## 输入清单

| 文件 | 说明 |
|------|------|
| inputs/case001_reference.md | 前案与证据来源说明 |
| inputs/phase1_jd_pool.csv | Phase1 JD 池 |
| inputs/phase1_jd_pool_summary.md | 分桶统计摘要 |
| inputs/resume_summary.md | 脱敏简历摘要 |

## Owner 批准记录

- **2026-06-03**：Owner 指令「你继续处理」→ Phase2 执行授权生效（见 `07`）。

## 不适用说明

- 不投递、不 cron、不把 tier 当执行令。
