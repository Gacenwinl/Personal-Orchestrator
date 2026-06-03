---
case_id: CASE-001-mems-career-direction
rule_ref: registry/mode_selector_rules.yaml
generated_by: scripts/suggest_modes.py
pre_execution: false
---

# Mode Selection

## 模式序列（有序）

1. dynamic_assembly
2. parallel_debate
3. career_fit_matrix
4. cross_team_conflict_detector
5. jury_panel
6. meta_review

## 选择理由

- rule_1: case_type=career_direction, needs_execution=True — 方向案先并行再矩阵收敛
- rule_2: case_type=career_direction, risk_tier=high

## 模式要求的团队

- critical_assumption

## 预计时间成本

- TODO: Orchestrator 结合案件复杂度填写。

## 模型分配（工作流测试：见 model_defaults.yaml / WORKFLOW_TEST_MIMO.md）

| 步骤 | vendor | 角色 |
|------|--------|------|
| Orchestrator（Cursor） | xiaomi | 立案/调度/验收 |
| parallel_debate（各 team） | xiaomi | mimo-v2.5-pro — 04 评审块 |
| jury_panel | xiaomi | mimo-v2.5-pro — 汇总 |
| critical_assumption | xiaomi | mimo-v2.5-pro — CAC |
| meta_review（可选） | xiaomi | mimo-v2.5-pro — 工作流测试期同模型 |
