---
case_id: CASE-001-mems-career-direction
rule_ref: registry/mode_selector_rules.yaml
---

# Mode Selection

## 模式序列（有序）

1. dynamic_assembly
2. parallel_debate
3. career_fit_matrix
4. cross_team_conflict_detector
5. jury_panel

## 选择理由

- 方向案需多视角并行，再用矩阵收敛 fit。
- 高风险的 `critical_assumption` 团队在 parallel 后进入 06 专卷（非替代 04 块）。
- 执行前未跑 `execution_handoff_review`（当时未起草 09）；Phase1 授权后在 09 草案上补审。

## 预计时间成本

- 审理约 90 分钟；Phase1 执行约 4–6 小时（Hermes 或等效手工）。

## 模型分配（Phase 1 手填）

| 步骤 | vendor | 角色 |
|------|--------|------|
| parallel 正方倾向 | anthropic | 战略/叙事 |
| parallel 结构化 | openai | 矩阵/前提 |
| jury_panel | anthropic | 综合 |
