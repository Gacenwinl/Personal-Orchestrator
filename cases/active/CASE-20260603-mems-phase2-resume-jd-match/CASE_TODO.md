# CASE-20260603-mems-phase2-resume-jd-match 下一步

## 当前状态

- `instruction_issued` — Phase2 已授权，`09` 与 HANDOFF 已生成。

## Owner / Hermes

1. 打开 `artifacts/HANDOFF_hermes_phase2.md`，按 [integrations/hermes_handoff_checklist.md](../../../integrations/hermes_handoff_checklist.md) 手工交给 Hermes。
2. 执行后由 Executor 填写 `10_execution_feedback.md`。

## Orchestrator（执行后）

1. 独立验收 `11_acceptance_review.md`（对照 `09` 与 B 系列）。
2. `python3 scripts/validate_case.py cases/active/CASE-20260603-mems-phase2-resume-jd-match`
3. 通过后再考虑 `status: completed` 与 `12` lesson 升格。
