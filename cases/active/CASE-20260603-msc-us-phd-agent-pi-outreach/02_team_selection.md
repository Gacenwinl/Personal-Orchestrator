---
case_id: CASE-20260603-msc-us-phd-agent-pi-outreach
rule_ref: registry/team_selector_rules.yaml
---

# Team Selection

> **Registry 适配说明：** 默认 `technical_route` 不含学术市场与 AI agent 工作流队；测试案手工增选。

## 选用团队

| team_id | 理由 |
|---------|------|
| technical_depth | Robotics + AI agent 方向匹配、研究深度门槛 |
| career_strategy | 美国 PhD 路径与 MSc 定位（非求职 JD） |
| evidence_audit | 本科/MSc 证据链是否支撑套瓷叙事 |
| critical_assumption | 高风险路径前提与翻转条件 |
| risk_control | 时间线、签证、声誉与套瓷伦理风险 |
| ai_workflow | Agent 研究方向可执行性与工具链现实性 |
| jury_panel | 收敛分歧 |

## 规则命中 + 手工扩展

| team_id | 来源 |
|---------|------|
| technical_depth, evidence_audit, critical_assumption, risk_control, jury_panel | rule_2 `technical_route` |
| career_strategy, ai_workflow | **手工增选**（学术路径测试） |

## 未选用团队

| team_id | 未选理由 |
|---------|----------|
| simulation_engineering | 本案非 MEMS/仿真求职；机器人仿真仅在 technical_depth 覆盖 |
| jd_matching, resume_packaging | 求职域；本案为学术套瓷 |
| market_reality | 未单独拉队；career_strategy + risk_control 覆盖 PhD 市场 |
| thermal_analysis 等 | 与 AI agent 套瓷路径无直接关系 |

## 冲突预期

- career_strategy（广撒网套瓷）vs risk_control（声誉/精准度）
- ai_workflow（追热点 agent）vs technical_depth（需扎实 robotics 基础）
