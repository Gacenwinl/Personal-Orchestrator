---
case_id: CASE-001-mems-career-direction
execution_authorized: true
---

# Phase Plan

## Phase 列表

| phase | 目标 | 依赖 | 是否需授权 |
|-------|------|------|------------|
| phase1 | 收集 20 条 JD，分桶+字段完整 | CAC A1–A2 | 已授权 |
| phase2 | 方向决策/简历改写 | phase1 验收 + 新 CAC | 未授权 |

## 停止条件（全局）

- 触发登录/验证码/风控 → 停止回报。
- 满 20 条有效详情页 JD 可提前结束。

## 不做什么

- 不投递、不填表、不评价「已安排 cron」。
