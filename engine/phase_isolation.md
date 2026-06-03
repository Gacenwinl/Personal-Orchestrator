# Phase Isolation

## 原则

长程任务污染来自：**同一会话**里既做战略评审又做大量执行细节。本 Harness 用**文件**换**上下文**。

## 纯文本规则

1. **Session 审理**：只打开 `00`–`07`、`02b`、`artifacts/team_blocks/`。不打开 Hermes 日志、不跑爬虫。
2. **Session 执行**：只打开当前 Phase 的 `08`、`09`、约定 `inputs/`。不重新辩论方向，除非 11 触发 `reopen_court`。
3. **Session 验收**：只打开 `09`、`10`、产物路径。对照 `11` checklist，不信 Executor 摘要。
4. **Session 沉淀**：只打开 `11`、`12` 与 `lessons/`。

## Phase 文件

推荐结构：

```
cases/active/CASE-xxx/
  phases/
    phase1/
      09_executor_instruction.md
      10_execution_feedback.md
      11_acceptance_review.md
```

或单文件命名：`09_executor_instruction_phase1.md`。

## Local Executor 例外

当 Cursor 修改 **本仓库** `registry/`、`templates/`、`prompts/` 时：

- 视为 **Local Executor**，不是审理 Session。
- 不得在同一 turn 里既改 registry 又填写活跃 case 的 04 块（避免规则与案件混淆）。

## External Executor

Hermes / OpenClaw 会话**只接收** `09` 的副本或路径引用，不加载完整法庭记录（除非 Orchestrator 显式附加摘要）。
