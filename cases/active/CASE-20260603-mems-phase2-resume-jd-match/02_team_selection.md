---
case_id: CASE-20260603-mems-phase2-resume-jd-match
rule_ref: registry/team_selector_rules.yaml
generated_by: scripts/suggest_teams.py
---

# Team Selection

## 选用团队

| team_id | 理由 |
|---------|------|
| career_strategy | Phase2 核心：是否从「探索组合」升为可执行主轴或降级岗族 |
| market_reality | 基于 Phase1 分桶（仿真 9 / 封装 6）评估竞争与 HC 结构 |
| jd_matching | Phase2 主战场：简历条目与 JD 职责/关键词对齐矩阵 |
| resume_packaging | 评估改写范围与可表达性，不先行乐观包装 |
| simulation_engineering | 校验仿真岗 JD 与项目算例可信度，防假阳性 |
| evidence_audit | 审计 Phase1 池与简历主张是否可被 JD 摘录支撑 |
| critical_assumption | 高风险 + RECOMMENDED+ 强制新 CAC（B 系列前提） |
| jury_panel | 汇总分歧，防止「有池即可主攻」的跳跃结论 |

## 未选用团队

| team_id | 未选理由 |
|---------|----------|
| hr_screening | Phase2 前无需 HR 筛选用语深拆；若简历定稿后再开 |
| cost_benefit | 时间成本已在 02b 模式链估算；无资金决策点 |
| human_approval | 由案件 frontmatter `human_approval_required: true` 覆盖，不单列法庭队 |
| interview_assessment | 无面试日程；属 Phase3+ |
| execution_handoff | 本轮 `execution_authorized: false`，授权后再加 pre_execution 队 |

## 规则命中

- rule_1: `case_type=career_direction`, `risk_tier=high`

## 冲突预期

- `resume_packaging` vs `evidence_audit`：改写力度
- `career_strategy` vs `market_reality`：是否现在锁定主轴
- `jd_matching` vs `simulation_engineering`：仿真岗匹配口径
