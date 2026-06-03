---
case_id: CASE-001-mems-career-direction
status: completed
case_type: career_direction
risk_tier: high
topic: 是否主攻 MEMS/封装/仿真求职方向；是否授权 Phase1 JD 收集
owner_intent_ref: 00_owner_intent.md

needs_execution: true
execution_authorized: true
authorized_phase: phase1
human_approval_required: false

court_verdict_tier: RECOMMENDED_WITH_MODIFICATIONS
cac_required: true
cac_exempt_reason: null
---

# Case Intake

## 案件摘要

评估「主攻 MEMS/封装/仿真」作为求职主轴是否合理；若合理，仅授权 Phase1：收集约 20 条相关 JD 并结构化，不登录不投递。

## 成功标准

- 法庭给出带前提的方向 verdict（非执行令）。
- CAC 列出可验证前提与验证顺序。
- Phase1 产物：20 条 JD 表（字段完整、链接为岗位详情页）。
- Orchestrator 独立验收通过或明确返工。

## 约束与时间预算

- 审理 Session：1–2 小时人工+Cursor。
- Phase1 执行：Owner 已批准，预算 1 个工作日 Hermes/手工等效。

## 输入清单

| 文件 | 说明 |
|------|------|
| inputs/resume_summary.md | 脱敏简历摘要 |
| inputs/sample_jd_notes.md | 2 条样例 JD 观察 |

## 不适用说明

- 不修改 Hermes 配置；不自动 cron；不填表提交。
