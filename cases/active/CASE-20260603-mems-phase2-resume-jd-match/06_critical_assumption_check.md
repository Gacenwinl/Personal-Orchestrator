---
case_id: CASE-20260603-mems-phase2-resume-jd-match
cac_status: complete
team_ref: critical_assumption
---

# Critical Assumption Check（Phase2 新案）

> Phase1 前提（A1–A5）在 CASE-001 中处理；本案仅列 **B 系列** Phase2 依赖前提。

## 结论依赖的前提

| id | 前提 | type | 验证方式 | 若错误则裁决 |
|----|------|------|----------|--------------|
| B1 | 简历能在 packaging+mixed 桶各找到 ≥3 条「强匹配」JD（duty 级） | unknown | fit 矩阵 + 人工标注 | 不升主轴，扩大岗族 |
| B2 | 组合叙事「封装协作+仿真验证」覆盖池内 ≥50% 目标投递桶 | inference | 矩阵覆盖率统计 | MODIFY 为单桶策略 |
| B3 | 至少 1 个算例路径可在材料中展示（报告/图/脚本） | inference | 本地材料清单 | 暂停改版，先补算例 |
| B4 | 目标城市在池内（或补充池后）仍有 ≥12 条可投 JD | unknown | 地域标注列 | 扩大地域或改行业 |
| B5 | 5 条抽样 JD 人工读后仍支持组合主轴（非关键词假阳性） | unknown | excerpt 对照表 | 降仿真权重或 REJECT 主轴 |

## Phase1 继承（仅引用，不重复验证）

| id | 状态 | 说明 |
|----|------|------|
| A1 | satisfied（金样例） | 20 条有效池；真实执行后需重验 |
| A4 | partial | 仿真占比 45%，本案 B5 加强验证 |

## 验证优先级

1. B5（假阳性）
2. B1（强匹配）
3. B3（算例）
4. B4（地域）

## 人工确认项

- Owner 确认：是否接受金样例池作为 Phase2 审理输入；若否，替换 `phase1_jd_pool.csv` 后再批准执行。
- Owner 确认：Phase2 是否包含「本地简历改写草稿」（仍须 `execution_authorized` 后才可做）。

## 翻转测试

- 若 B1 失败（强匹配 <3/桶）→ 法庭结论应降为 **MODIFY**：仅「继续探索」，禁止对外主轴表述。
- 若 B5 失败 → 仿真桶降权，优先 packaging/mixed 投递策略。
