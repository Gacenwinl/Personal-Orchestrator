# Scripts

## smoke_test.py

一键本地回归：验证 CASE-001、运行团队/模式建议、编译脚本、在临时目录创建 `--prepare` case 并检查关键文件。

```bash
python3 scripts/smoke_test.py
```

## case_status.py

查看单个 case 的可审计链路进度、缺失文件和下一步建议。

```bash
python3 scripts/case_status.py cases/samples/CASE-001-mems-career-direction
```

## render_case_dashboard.py

从案件 Markdown 生成单文件 HTML 看板（链路进度、辩论过程、team_blocks、CAC、授权闸门）。

```bash
python3 scripts/render_case_dashboard.py cases/active/CASE-xxx --force
python3 scripts/render_case_dashboard.py --index --force
```

输出：`artifacts/CASE_DASHBOARD.html`；索引：`cases/index.html`。

## check_registry.py

校验 `registry/` 内团队、模式和规则引用是否一致。

```bash
python3 scripts/check_registry.py
```

## list_cases.py

列出 `cases/active` 与 `cases/samples` 下的案件及 `status` / `risk_tier`。

```bash
python3 scripts/list_cases.py
```

## scaffold_team_blocks.py

根据 `02_team_selection.md` 的「选用团队」表，为每个 team 生成 `artifacts/team_blocks/<team_id>.md` 骨架。

```bash
python3 scripts/scaffold_team_blocks.py cases/active/CASE-xxx
python3 scripts/scaffold_team_blocks.py cases/active/CASE-xxx --force
```

## render_handoff.py

从 `09_executor_instruction.md` 生成 Hermes 交接包（不自动执行、不建 cron）。

```bash
python3 scripts/render_handoff.py cases/active/CASE-xxx
python3 scripts/render_handoff.py cases/samples/CASE-001-mems-career-direction --force
```

## check_templates.py

校验 `templates/` 内 00–12 核心模板是否齐全，并检查关键授权/验收/lesson 字段是否存在。

```bash
python3 scripts/check_templates.py
```

## new_case.py

从一个 topic 创建本地 Markdown 案件骨架，只写入 `cases/active/`，不调用模型、API、Hermes 或外部任务。

用法：

```bash
python3 scripts/new_case.py "是否主攻 MEMS/封装/仿真方向？" --case-type career_direction --risk-tier high --needs-execution --prepare
```

输出新 case 目录路径。加 `--prepare` 时会同时生成 `02_team_selection.md` 与 `02b_mode_selection.md` 草稿。

## validate_case.py

校验单个 case 目录是否满足 Harness 的机械规则：

- `01_case_intake.md` frontmatter 必填字段
- `needs_execution / execution_authorized / authorized_phase / human_approval_required` 四字段
- 可审计链路文件是否齐全
- `critical_assumption` 与 `06_critical_assumption_check.md` 是否按规则触发
- 已授权执行案件的 `09` / `10` / `11` 是否齐全
- `09_executor_instruction.md` 的 phase 与授权 phase 是否一致

用法：

```bash
python3 scripts/validate_case.py cases/samples/CASE-001-mems-career-direction
```

返回码：

- `0`：无 ERROR
- `1`：存在 ERROR，案件不得标记 `completed`

## 下一步脚本

## suggest_teams.py

读取 `01_case_intake.md` 与 `registry/team_selector_rules.yaml`，输出命中的规则、必选团队和可选团队。它只辅助 Orchestrator 写 `02_team_selection.md`，不替代人工理由。

用法：

```bash
python3 scripts/suggest_teams.py cases/samples/CASE-001-mems-career-direction
python3 scripts/suggest_teams.py cases/samples/CASE-001-mems-career-direction --pre-execution
python3 scripts/suggest_teams.py cases/active/CASE-xxx --write
```

返回码：

- `0`：找到规则且无机械冲突
- `1`：读取失败或规则冲突
- `2`：未匹配任何规则

## suggest_modes.py

读取 `01_case_intake.md` 与 `registry/mode_selector_rules.yaml`，输出命中的规则、建议模式序列与模式附带要求的团队。它辅助 Orchestrator 写 `02b_mode_selection.md`。

用法：

```bash
python3 scripts/suggest_modes.py cases/samples/CASE-001-mems-career-direction
python3 scripts/suggest_modes.py cases/samples/CASE-001-mems-career-direction --pre-execution
python3 scripts/suggest_modes.py cases/active/CASE-xxx --write
```

返回码同 `suggest_teams.py`。