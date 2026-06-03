---
case_id: CASE-001-mems-career-direction
cac_status: complete
team_ref: critical_assumption
---

# Critical Assumption Check

## 结论依赖的前提

| id | 前提 | type | 验证方式 | 若错误则裁决 |
|----|------|------|----------|--------------|
| A1 | 目标地域 3 个月内存在 ≥15 条可投「对口」JD | unknown | Phase1 收集+分桶 | 从 RWM 降为 MODIFY/REJECT 主轴 |
| A2 | JD 学历/年限门槛用户可满足 ≥60% 样本 | inference | 逐条标注 | 改推相邻岗族 |
| A3 | 简历能在 2 个项目内表达仿真/封装相关交付 | inference | resume_packaging 对照 JD | 先改简历再谈方向 |
| A4 | 纯仿真岗占比 <40%（否则竞争过激） | unknown | 分桶统计 | 改组合策略 |
| A5 | 存在比「仿真主轴」更优的相邻方向（器件/可靠性） | unknown | 同事位族对比矩阵 | 可能翻转主轴 |

## 验证优先级

1. A1（JD 池规模与对口定义）
2. A2（门槛）
3. A4（结构占比）

## 人工确认项

- Owner 确认目标城市列表与「对口」操作定义。

## 翻转测试

- 若 A1 不成立（<10 条对口 JD），则不应「主攻」仿真/封装，应 `MODIFY` 为「扩大岗位族或地域」。
