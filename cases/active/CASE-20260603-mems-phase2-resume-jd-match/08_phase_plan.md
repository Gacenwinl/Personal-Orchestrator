---
case_id: CASE-20260603-mems-phase2-resume-jd-match
execution_authorized: false
---

# Phase Plan

## Phase 列表

| phase | 目标 | 依赖 | 是否需授权 |
|-------|------|------|------------|
| phase1 | （前案 CASE-001）JD 池 20 条 + 分桶 | CASE-001 验收 | 已在金样例完成 |
| phase2 | fit 矩阵、5 条 excerpt、简历 v2 草稿、方向决策备忘 | 06 B 系列 + Owner 批准 | **未授权** |

## Phase2 执行范围（授权后）

- 产出 `outputs/fit_matrix.md`、`outputs/resume_v2_draft.md`（路径在 `09` 中细化）。
- 禁止：投递、登录、自动 cron。

## 停止条件（全局）

- 触发登录/验证码/风控 → 停止回报。
- evidence_audit 发现 bullet 无 JD 依据 → 停止改版。

## 不做什么

- 不替代 Owner 批准。
- 不在本 plan 文件中写入执行授权。
