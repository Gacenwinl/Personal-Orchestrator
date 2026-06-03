---
case_id: CASE-20260603-mems-phase2-resume-jd-match
phase: phase2
executor_target: hermes
execution_authorized: true
human_approval_required: false
generated_by: scripts/render_handoff.py
---

# Hermes Handoff Packet

> **这不是 court verdict，也不是自动执行令。** 仅当 `execution_authorized: true` 且 Owner 已按需审批后，才可交给 Hermes。

## 授权检查

| 项 | 值 |
|----|-----|
| execution_authorized | True |
| authorized_phase | phase2 |
| human_approval_required | False |
| court_verdict_tier | RECOMMENDED_WITH_MODIFICATIONS |

## 交给 Hermes 前确认

- [ ] 已读 `constraints/HARNESS_ENGINE.md`
- [ ] `09` 中 forbidden_actions 与 Hermes profile 白名单一致
- [ ] 不修改 Hermes 源码，不自动创建 cron（除非你明确批准）
- [ ] 执行后只更新 Harness `10_execution_feedback.md`，由 Orchestrator 填 `11`

## 任务书原文

---
case_id: CASE-20260603-mems-phase2-resume-jd-match
phase: phase2
executor_type: external
executor_target: hermes
execution_authorized: true
human_approval_required: false
---

# Executor Instruction

> External Executor：Hermes 或 Owner 指定手工等效。**非** court verdict 自动执行。  
> 验证 CAC B1–B5；**不得**对外宣布「主攻」或投递。

## Phase 目标

1. 产出 **fit 矩阵**（JD 池 × 简历对齐，含 gap 标记）。
2. **5 条** JD 人工读后 excerpt + 与简历 bullet 对照（验证 B5）。
3. **简历 v2 草稿**（仅本地文件，组合叙事「封装协作 + 仿真验证」）。
4. **方向决策备忘**（是否升为组合主轴候选；若 B1/B5 失败则明确 MODIFY 建议）。

## 输入文件

- `inputs/phase1_jd_pool.csv`
- `inputs/phase1_jd_pool_summary.md`
- `inputs/resume_summary.md`
- `inputs/case001_reference.md`
- `06_critical_assumption_check.md`（B 系列）

## 执行步骤

1. 读取 CSV；对 `packaging`、`mixed`、`simulation_cae` 三桶各标注强/中/弱匹配（duty 级，非仅标题关键词）。
2. 从三桶各抽至少 1 条、合计 **5 条** JD：人工读职责，写入 excerpt 表（公司、title、job_url、jd_excerpt、match_rationale）。
3. 生成 `outputs/fit_matrix.md`（含每桶强匹配计数，对照 B1）。
4. 生成 `outputs/jd_excerpt_table.md`（5 条，对照 B5）。
5. 基于矩阵与 excerpt，起草 `outputs/resume_v2_draft.md`（不夸大；每条 bullet 标注对应 JD id 或「待补算例」）。
6. 生成 `outputs/direction_memo.md`：组合主轴候选 / 降级岗族 / 待补 B3 算例清单。
7. 将执行事实写入 `10_execution_feedback.md`（路径、条数、阻塞项）。

## 输出文件

| 路径 | 格式 | 必填字段 |
|------|------|----------|
| outputs/fit_matrix.md | md | bucket, jd_id, align_strong/med/weak, gap_note |
| outputs/jd_excerpt_table.md | md | company, title, job_url, jd_excerpt, resume_bullet_ref |
| outputs/resume_v2_draft.md | md | sections + jd_ref per bullet |
| outputs/direction_memo.md | md | decision, b1_b5_status, next_owner_action |

## 禁止事项（forbidden_actions）

- 不登录招聘站、不填表、不投递、不发邮件
- 不删未备份文件、不修改 Hermes/OpenClaw 配置、不创建 cron
- 不扩大 scope（未列步骤不做）
- 不对外发布简历、不宣称「已主攻 MEMS/仿真」

## 失败处理

- 单站需登录/验证码 → 跳过该条并记录，不绕过风控。
- B5 抽样后若 3/5 不支持组合主轴 → 在 direction_memo 建议 MODIFY，仍完成矩阵与草稿。

## 验收标准（Orchestrator 将据此填 11）

- `fit_matrix.md` 存在且 packaging+mixed 强匹配计数可核对 B1。
- `jd_excerpt_table.md` 恰好 5 条，含 verbatim 职责摘录。
- `resume_v2_draft.md` 每条 bullet 有 jd_ref 或「待补算例」。
- `direction_memo.md` 明确组合候选或降级建议。
- 无 forbidden 行为；`10` 已填事实路径。

## 停止并回报条件

- 遇验证码/登录要求 → 立即停止并写 `10`。
- evidence 无法追溯 → 停止改版，在 `10` 列出缺口。


## 执行后回报

请将结果写入本案：

- `cases/active/CASE-20260603-mems-phase2-resume-jd-match/10_execution_feedback.md`
- 产物放到 `outputs/` 下约定路径
