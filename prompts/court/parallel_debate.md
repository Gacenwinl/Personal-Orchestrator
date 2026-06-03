# 调用壳：parallel_debate

1. 读 `registry/debate_modes.yaml` 中 `parallel_debate`。
2. 对 `02_team_selection.md` 中每个 `team_id`：
   - 读 `registry/teams/<team_id>.yaml`
   - 输出到 `artifacts/team_blocks/<team_id>.md`，**严格**使用 `templates/04_team_verdict_block.md` frontmatter 与章节。
3. 禁止在本模式生成 `09_executor_instruction` 或设置 `execution_authorized: true`。
