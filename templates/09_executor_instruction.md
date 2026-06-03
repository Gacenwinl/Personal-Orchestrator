---
case_id: ""
phase: phase1
executor_type: external
executor_target: hermes
delivery_profile: default
execution_authorized: false
human_approval_required: true
---

# Executor Instruction

> **External Executor**（Hermes/OpenClaw）专用。Cursor 维护本仓库时用 Local Executor，不得使用本模板对外执行。

## Phase 目标

- 

## 输入文件

- 

## 执行步骤

1. 

## 输出文件

| 路径 | 格式 | 必填字段 |
|------|------|----------|
| | | |

## 禁止事项（forbidden_actions）

- 不登录、不填表、不提交、不删文件、不扩 scope

## 失败处理

- 

## 验收标准（Orchestrator 将据此填 11）

- 

## 停止并回报条件

- 

## 上游依赖（upstream_depends_on）

- 

## 下游门控（downstream_gates）

- 10_execution_feedback.md（Executor 填写完成后）
- 11_acceptance_review.md（Orchestrator 独立验收）
- 12_lesson_proposal.md

## 执行上下文摘要（execution_context）

> 来自 05_court_summary + 07_orchestrator_decision 的关键结论（最多 2000 字）

- 

## 失败策略（failure_strategy）

| 场景 | 处理方式 |
|------|----------|
| 超时/挂起 | 停止并回报 Orchestrator |
| 产出不达标 | 写部分输出 + gap 日志，不自行扩 scope |
| 连续相同错误（≥3次） | 停止 + 写 daemon_error.log |

## 回退检查点（rollback_to）

- 回退至：`07_orchestrator_decision.md`（最后已知 OK 状态）
