---
case_id: CASE-001-mems-career-direction
rule_ref: registry/team_selector_rules.yaml
---

# Team Selection

## 选用团队

| team_id | 理由 |
|---------|------|
| career_strategy | 方向是否值得作为主轴 |
| market_reality | JD 池与竞争强度 |
| jd_matching | 背景与岗位族匹配 |
| resume_packaging | 项目能否支撑简历叙事 |
| simulation_engineering | 仿真/封装岗位映射 |
| evidence_audit | 区分事实与推断 |
| critical_assumption | **核心**：前提与翻转（第一批必选） |
| jury_panel | 综合收敛 |

## 未选用团队（须列至少 3 个）

| team_id | 未选用理由 |
|---------|------------|
| thermal_analysis | 本案未聚焦热仿真子赛道 |
| electromagnetic_analysis | 未以 EM 为主轴提问 |
| ai_workflow | 非自动化架构案 |
| interview_assessment | Phase1 前不需面试深拆 |
| chip_packaging | 已由 simulation_engineering + market 覆盖封装岗族，避免重复 |

## 规则命中

- matched_rule: `case_type: career_direction` + `risk_tier: high`

## 冲突预期

- resume_packaging vs market_reality：可包装性 vs 真实岗位量
