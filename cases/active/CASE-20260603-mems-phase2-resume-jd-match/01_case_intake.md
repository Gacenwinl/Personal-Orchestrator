---
case_id: CASE-20260603-mems-phase2-resume-jd-match
status: orchestrator_decided
case_type: career_direction
risk_tier: high
topic: "在 CASE-001 Phase1 结论与 JD 池证据基础上，评估是否进入 Phase2（方向决策 / 简历与 JD 匹配深化）；本轮仅审理，不授权对外执行。"
owner_intent_ref: 00_owner_intent.md
predecessor_case: CASE-001-mems-career-direction

needs_execution: true
execution_authorized: false
authorized_phase: null
human_approval_required: true

court_verdict_tier: RECOMMENDED_WITH_MODIFICATIONS
cac_required: true
cac_exempt_reason: null
---

# Case Intake

## 案件摘要

在 CASE-001 Phase1（JD 池 mock 20 条、分桶完成）与「先证据后主攻」结论基础上，评估是否授权 **Phase2**：方向决策（是否升为组合主轴/是否降级相邻岗族）及简历与 JD 匹配深化；**本轮 Session 仅审理，不对外执行**。

## 成功标准

- 法庭给出 Phase2 可执行的 verdict 与前提（非执行令）。
- 新 CAC（B1–B5）列出可验证前提与验证顺序。
- `07` 明确：`execution_authorized: false`，待 Owner 批准后再写 `09`。
- `validate_case.py` 无 ERROR。

## 约束与时间预算

- 审理 Session：约 1–2 小时（Cursor Orchestrator + 你阅结论）。
- Phase2 执行预算：待授权后另计（Hermes/手工）；本轮不启动。

## 输入清单

| 文件 | 说明 |
|------|------|
| inputs/case001_reference.md | 前案与证据来源说明 |
| inputs/phase1_jd_pool.csv | Phase1 JD 池（金样例复制） |
| inputs/phase1_jd_pool_summary.md | 分桶统计摘要 |
| inputs/resume_summary.md | 脱敏简历摘要 |

## 不适用说明

- 不登录招聘站、不投递、不自动 cron。
- 不修改 Hermes/OpenClaw 配置。
- 不把 `court_verdict_tier` 当作 Phase2 执行授权。
