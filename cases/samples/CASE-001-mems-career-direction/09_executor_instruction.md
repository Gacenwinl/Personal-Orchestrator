---
case_id: CASE-001-mems-career-direction
phase: phase1
executor_type: external
executor_target: hermes
execution_authorized: true
human_approval_required: false
---

# Executor Instruction

> External Executor：Hermes（或 Owner 指定）。**非** court verdict 自动执行。

## Phase 目标

收集 **20 条** MEMS/封装/仿真/相关器件工程校招或社招 JD，结构化整理，用于验证 CAC A1/A2/A4。

## 输入文件

- `inputs/resume_summary.md`
- `inputs/sample_jd_notes.md`

## 执行步骤

1. 在公开校招/社招页搜索关键词组合（MEMS、封装、先进封装、CAE、仿真工程师等），**不登录**。
2. 每条记录：公司、岗位名、城市、学历、年限、JobLink（**岗位详情页**）、JD 摘要（verbatim 核心职责）。
3. 分桶：`packaging` / `mems_process` / `simulation_cae` / `mixed` / `other`。
4. 输出 `outputs/jd_pool_phase1.md` 与 `outputs/jd_pool_phase1.csv`。

## 输出文件

| 路径 | 格式 | 必填字段 |
|------|------|----------|
| outputs/jd_pool_phase1.csv | csv | company, title, city, degree, years, bucket, job_url, jd_excerpt |
| outputs/jd_pool_phase1.md | md | 同上 + 统计摘要 |

## 禁止事项（forbidden_actions）

- 不登录、不填表、不提交、不删文件、不修改 Hermes/OpenClaw 配置、不扩 scope

## 失败处理

- 单站反爬失败 → 跳过并记录，不绕过风控。

## 验收标准（Orchestrator 将据此填 11）

- 有效条目 ≥20；JobLink 均为详情页；bucket 统计完整；无 forbidden 行为。

## 停止并回报条件

- 遇验证码/登录要求 → 立即停止并写 10。
