# harness-court-team

**适用 profile:** `court-team`（并行评审工人）、`court-verify`（验证器）、`court-synthesize`（综合器）

## 用途

作为 Hermes kanban swarm 的工人技能（skill），为 Personal-Orchestrator-Harness 的法庭评审流程提供：

1. 单队评审执行（`court-team` profile 使用）
2. 评审块完整性验证（`court-verify` profile 使用）
3. 多队汇总 + 冲突检测（`court-synthesize` profile 使用）

**非侵入原则：** 本 skill 只读写 Harness 仓库的 `cases/` 目录，不修改 Hermes 源码、不调用非 MiMo 外部服务、不触发提交/投递/删除。

---

## 任务标题格式（kanban swarm 约定）

kanban 任务标题必须遵守：

```
{team_id}::{case_dir_abs}
```

示例：`career_strategy::/Users/openclaw/Personal-Orchestrator-Harness/cases/active/CASE-20260603-xxx`

skill 从任务标题中解析这两个字段；若格式不符则停止并报错。

---

## Role A — 单队评审（court-team profile）

### 执行步骤

1. **解析任务标题** → 取得 `team_id` 和 `case_dir_abs`

2. **读取团队配置**（只读）
   ```
   {harness_root}/registry/teams/{team_id}.yaml
   ```
   提取：`mandate`、`scoring_dimensions`、`common_misjudgments`、`conflicts_with`

3. **读取案件材料**（只读）
   - `{case_dir}/01_case_intake.md`（案件定义、风险级别）
   - `{case_dir}/03_debate_session.md`（已有讨论上下文，如存在）

4. **读取输出模板**
   ```
   {harness_root}/templates/04_team_verdict_block.md
   ```

5. **构建评审 prompt**（格式见下方）并调用当前会话模型（MiMo）完成评审

6. **写输出**（写前备份）
   - 备份：若 `{case_dir}/artifacts/team_blocks/{team_id}.md` 已存在，先复制到 `{case_dir}/artifacts/{team_id}.bak`
   - 写入：`{case_dir}/artifacts/team_blocks/{team_id}.md`

7. **复杂子任务委托**（sub-agent delegate 条件）
   若评审过程中发现需要独立的深度调研（例如：市场数据核查、技术可行性验证），且该子任务可独立闭环，则：
   - 在 kanban board `orchestrator-court` 创建子任务，标题格式：`{team_id}-subtask::{case_dir_abs}::{subtask_desc}`
   - 将子任务结果等待完成后合并进主评审块
   - **禁止** 为同一子任务创建超过 2 层嵌套委托

### 评审 Prompt 模板

```
你是 {mandate}（team_id: {team_id}）评审专家。

【案件背景】
{01_case_intake_body}

【讨论上下文】
{03_debate_body_or_empty}

【你的专业职责】
{mandate}

【评审维度】
{scoring_dimensions}

【常见误判提醒】
{common_misjudgments}

【冲突预期（与以下团队可能有分歧）】
{conflicts_with}

【输出要求】
严格按照以下 YAML frontmatter + Markdown 结构输出，不添加额外内容：

---
case_id: {case_id}
team_id: {team_id}
team_verdict_tier: <IMMEDIATELY_RECOMMENDED|RECOMMENDED|RECOMMENDED_WITH_MODIFICATIONS|MODIFY|REJECT>
confidence: <high|medium|low>
registry_ref: registry/teams/{team_id}.yaml
---

# Team Verdict Block — {team_id}

## Scores（1–5）
| dimension | score | note |
|-----------|-------|------|
{dimensions_table}

## Findings
- <3–6 条事实性发现>

## Risks
- <2–4 条风险，注明 severity: P0/P1/P2>

## Assumptions
| assumption | type | note |
|------------|------|------|

## Conflicts noted（与其他团队）
- <与 {conflicts_with} 的潜在分歧>

## Recommended next step（评审建议，非执行令）
- <具体建议，不含 execution_authorized 字段>

【禁止事项】
- 禁止在输出中写 execution_authorized、needs_execution 或任何授权决策字段
- 禁止写"立即执行"等执行令语气的结论
- confidence 不足时明确标 low，不伪装确定
```

---

## Role B — 评审块验证（court-verify profile）

### 执行步骤

1. 从 kanban 综合任务上下文读取所有 worker 已完成的 block 路径
2. 对每个 `{case_dir}/artifacts/team_blocks/{team_id}.md`：
   - 验证 frontmatter 包含所有 `verdict_schema.yaml` 的 `team_verdict_block_required_fields`
   - 验证 `team_verdict_tier` 为合法值
   - 验证没有 `execution_authorized` 字段
3. 失败的 block 写到 `{case_dir}/artifacts/court_verify_failures.json`
4. 输出 pass/fail 汇总（供 synthesizer 决定是否继续）

---

## Role C — 汇总综合（court-synthesize profile）

### 执行步骤

1. 读取所有通过验证的 `artifacts/team_blocks/*.md`
2. 执行 `cross_team_conflict_detector`：提取各队 `Conflicts noted` 并交叉比对
3. 执行 `jury_panel` 投票：按各队 `team_verdict_tier` 加权（IMMEDIATELY_RECOMMENDED=5 … REJECT=1）
4. 写 `{case_dir}/05_court_summary.md`（格式见下方），**不写** `execution_authorized`
5. 更新 `{case_dir}/01_case_intake.md` frontmatter 的 `court_verdict_tier` 字段（仅此字段）

### 综合输出格式

```yaml
---
case_id: {case_id}
court_verdict_tier: <加权多数结论>
confidence: <high|medium|low>
synthesized_by: court-synthesize/harness-court-team
---
```

```markdown
# Court Summary — {case_id}

## Summary
<2–3 句综合结论>

## Key Risks（跨队汇总）
- <P0 项>
- <P1 项>

## Cross-team Conflicts
| team_A | team_B | 分歧点 | 解决建议 |
|--------|--------|--------|----------|

## Jury Verdict
| team_id | tier | weight |
|---------|------|--------|

加权结论：{court_verdict_tier}

## Dissent
<少数派意见>

## Recommended next step（非执行令）
<Orchestrator 下一步建议>
```

---

## 硬约束（任何 role 均适用）

1. **禁止** 写 `execution_authorized`、`needs_execution`、`authorized_phase` 字段
2. **禁止** 发邮件、提交申请、修改 `registry/` 或 `constraints/` 目录
3. **禁止** 超出 `cases/` 目录的写操作
4. **禁止** 修改 `HARNESS_ENGINE.md` 或 `SOUL.md`
5. 所有写操作前先备份（`.bak` 机制）
6. 遇到格式异常的 block → 报错停止，不静默跳过

---

## 安装说明

```bash
# 在 Personal-Orchestrator-Harness 根目录执行：
make hermes-setup
# 等价手工命令：
hermes profile create court-team
hermes profile create court-verify
hermes profile create court-synthesize
hermes skills install scripts/skills/harness-court-team --as court-team
hermes skills install scripts/skills/harness-court-team --as court-verify
hermes skills install scripts/skills/harness-court-team --as court-synthesize
```

环境变量要求：`XIAOMI_API_KEY`（从 `~/.openclaw/.env` 读取，与 Hermes 共用）。
