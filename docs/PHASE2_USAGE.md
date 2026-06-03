# Phase 2 Usage — Local Helpers

本阶段把第一阶段 Markdown Harness 的部分机械步骤脚本化，但仍保持：

- 不调用外部 API
- 不自动执行 Hermes / OpenClaw
- 不修改远程仓库或系统配置
- 不替代 Orchestrator 的判断与理由书写

## 1. 从 topic 创建案件

```bash
python3 scripts/new_case.py \
  "是否主攻 MEMS/封装/仿真方向？" \
  --case-type career_direction \
  --risk-tier high \
  --needs-execution \
  --prepare
```

输出目录示例：

```text
cases/active/CASE-20260603-是否主攻-mems-封装-仿真方向
```

`--prepare` 会同时生成：

- `00_owner_intent.md`
- `01_case_intake.md`
- `02_team_selection.md`（草稿）
- `02b_mode_selection.md`（草稿）
- `CASE_TODO.md`

## 2. 重新生成团队/模式草稿

当你修改 `01_case_intake.md` 后，可以重跑：

```bash
python3 scripts/suggest_teams.py cases/active/CASE-xxx --write --force
python3 scripts/suggest_modes.py cases/active/CASE-xxx --write --force
```

注意：`--force` 会覆盖已有 `02` / `02b`。如果已经人工补充过理由，先备份或手工合并。

## 3. 继续审理

脚本只负责机械选择。Orchestrator 仍必须人工完成：

1. 在 `02_team_selection.md` 中补充选用与未选理由。
2. 在 `02b_mode_selection.md` 中补充时间成本与模型分配。
3. 生成各团队 `artifacts/team_blocks/*.md`。
4. 汇总 `05_court_summary.md`。
5. 高风险或 RECOMMENDED+ 案件填写 `06_critical_assumption_check.md`。
6. 在 `07_orchestrator_decision.md` 中明确执行授权四字段。

## 4. 结案前校验

```bash
python3 scripts/validate_case.py cases/active/CASE-xxx
```

`PASS` 才允许 `status: completed`。

## 5. 脚本边界

这些脚本只是 Local Executor，允许改本仓库 case 文件；它们不会：

- 创建 Hermes cron
- 访问 GitHub/飞书/Obsidian
- 登录网站
- 投递岗位
- 修改 `execution_authorized`
- 替代 Human Owner 审批
