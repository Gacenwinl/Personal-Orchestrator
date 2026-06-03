# Scripts

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

- `suggest_teams.py` — 读 `team_selector_rules.yaml` 输出建议团队列表