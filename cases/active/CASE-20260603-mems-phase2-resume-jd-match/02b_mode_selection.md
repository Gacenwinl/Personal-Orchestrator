---
case_id: CASE-20260603-mems-phase2-resume-jd-match
rule_ref: registry/mode_selector_rules.yaml
generated_by: scripts/suggest_modes.py
---

# Mode Selection

## 建议模式序列

| 顺序 | mode_id | 理由 |
|------|---------|------|
| 1 | dynamic_assembly | 高险方向案，先按 intake 组庭 |
| 2 | parallel_debate | 8 队并行基于 Phase1 池与简历辩论 |
| 3 | career_fit_matrix | Phase2 核心产出：分桶 × 简历匹配矩阵 |
| 4 | cross_team_conflict_detector | 锁定主轴 vs 继续探索的分歧 |
| 5 | jury_panel | 收敛法庭 tier |
| 6 | meta_review | 可选：若 B1/B2 前提争议大则升级（本案已执行摘要级） |

## 时间成本（估算）

- 并行辩论 + 矩阵：约 60–90 分钟 Orchestrator 填块
- Owner 阅 05/06/07：约 20 分钟
- **不含** Phase2 执行（简历改写/JD 深读）

## 未采用模式

| mode_id | 原因 |
|---------|------|
| execution_handoff_review | 未授权执行，留待 `09` 前 |

## 模型分配（工作流测试）

- 全团队块与汇总：Orchestrator 在 Cursor 填写；若拆 Session 可参考 [docs/WORKFLOW_TEST_MIMO.md](../../docs/WORKFLOW_TEST_MIMO.md) 与 `registry/model_routing_rules.yaml`（测试期 MiMo）。
